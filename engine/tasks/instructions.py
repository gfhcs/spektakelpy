import abc
import io
from io import StringIO

from util import check_type, check_types
from util.immutable import Immutable, Sealable, check_unsealed, check_sealed
from .interaction import InteractionState, Interaction
from .stack import Frame, StackState
from ..functional import Reference, EvaluationException, Term, Value
from ..functional.types import TBuiltin
from ..functional.values import VException, VProcedure, VInt
from ..intrinsic import IntrinsicProcedure
from ..task import TaskStatus


class InstructionException(Exception):
    """
    Raised when the execution of an instruction fails.
    """
    pass


class Instruction(Immutable, abc.ABC):
    """
    Models the smallest, atomic execution steps.
    """

    @abc.abstractmethod
    def execute(self, tstate, mstate):
        """
        Executes this instruction in the given state, leading to a new state, that in particular determines which
        instruction to execute next.
        This procedure may modify the given TaskState and MachineState objects.
        :param tstate: The unsealed TaskState object that this instruction is to be executed in.
        It must be part of the given machine state.
        Any references to task-local variables will be interpreted with respect to this task state.
        :param mstate: The unsealed MachineState object that this instruction is to be executed in.
        It must contain the given task state.
        """
        pass

    @abc.abstractmethod
    def enabled(self, tstate, mstate):
        """
        Decides if executing this instruction is going to modify *any* part of the machine state, i.e. if any progress
        will be made.
        :param tstate: The task state that this instruction is to be executed in. It must be part of the given machine
        state. Any references to task-local variables will be interpreted with respect to this task state.
        :param mstate: The machine state that this instruction is to be executed in. It must contain the given task
        state.
        :return: A boolean value indicating if executing the instruction will lead to *any* change in the machine state.
        """
        pass


class Update(Instruction):
    """
    An instruction that updates a part of the machine state.
    """

    def __init__(self, ref, term, destination, edestination):
        """
        Creates a new update instruction.
        :param ref: A Term evaluating to a Reference object, specifying which part of the state is to be updated.
        :param term: The Term object specifying how to compute the new value.
        :param destination: The index of the instruction that is to be executed after this one.
        :param edestination: The index of the instruction to jump to if this instruction causes an error.
        """
        super().__init__()
        self._ref = check_type(ref, Term)
        self._term = check_type(term, Term)
        self._destination = check_type(destination, int)
        self._edestination = check_type(edestination, int)

    def __str__(self):
        return "{} := {}".format(self._ref, self._term)

    def enabled(self, tstate, mstate):
        return True

    def hash(self):
        return hash((self._ref, self._term, self._destination, self._edestination))

    def equals(self, other):
        return isinstance(other, Update) \
               and (self._ref, self._term, self._destination, self._edestination) \
               == (other._ref, other._term, other._destination, other._edestination)

    @property
    def reference(self):
        """
        The Term specifying which part of the state is to be updated.
        """
        return self._ref

    @property
    def term(self):
        """
        The Term specifying how to compute the new value.
        """
        return self._term

    @property
    def destination(self):
        """
        The index of the instruction that is to be executed after this one was executed successfully.
        """
        return self._destination

    @property
    def edestination(self):
        """
        The index of the instruction that is executed after this one has caused an error.
        """
        return self._edestination

    def execute(self, tstate, mstate):
        top = tstate.stack[-1]
        top.instruction_index = self._destination
        try:
            ref = self._ref.evaluate(tstate, mstate)
            value = self._term.evaluate(tstate, mstate)
        except Exception as ee:
            tstate.exception = VException(pexception=ee)
            top.instruction_index = self._edestination
            return

        try:
            ref.write(tstate, mstate, value)
        except Exception as ex:
            tstate.exception = VException(pexception=ex)
            top.instruction_index = self._edestination


class Guard(Instruction):
    """
    An instruction that evaluates multiple boolean expressions and either blocks execution (if none of them are true)
    or proceeds with execution (if exactly one of them is true).
    If more than
    """

    def __init__(self, alternatives, edestination):
        """
        Creates a new guard instruction.
        :param alternatives: A mapping from Expression objects to integers, that specifies to which instruction index
                             to proceed in which case.
        :param edestination: The destination to jump to in case this instruction causes an error.
        """
        super().__init__()
        self._alternatives = {check_type(e, Term): check_type(d, int) for e, d in alternatives.items()}
        self._edestination = check_type(edestination, int)

    def __str__(self):
        with StringIO() as s:
            s.write("{")
            prefix = ""
            for t, d in self._alternatives.items():
                s.write(f"{prefix}{t}: {d}")
                prefix = ", "
            s.write("}")
            return s.getvalue()

    @property
    def conditions(self):
        """
        The expressions that this guard expression is evaluating.
        """
        return self._alternatives.keys()

    @property
    def destinations(self):
        """
        The instruction indices this guard expression may jump to, aligned with self.expressions.
        """
        return self._alternatives.values()

    @property
    def edestination(self):
        """
        The destination to jump to in case this instruction causes an error.
        """
        return self._edestination

    def hash(self):
        h = hash(self._edestination)
        for e, d in self._alternatives.items():
            h ^= hash((e, d))
        return h

    def equals(self, other):
        if not (isinstance(other, Guard) and self._edestination == other._edestination and
                len(self._alternatives) == other._alternatives):
            return False

        for e, d in self._alternatives.items():
            try:
                if other._alternatives[e] != d:
                    return False
            except KeyError:
                return False

        return True

    def enabled(self, tstate, mstate):
        return any(bool(e.evaluate(tstate, mstate)) for e in self._alternatives.keys())

    def execute(self, tstate, mstate):

        enabled = False

        top = tstate.stack[-1]

        for e, d in self._alternatives.items():

            try:
                r = bool(e.evaluate(tstate, mstate))
            except EvaluationException as ee:
                tstate.exception = VException(pexception=ee)
                top.instruction_index = self._edestination
                return

            if r:
                if enabled:
                    tstate.exception = VException(pexception=InstructionException("More than one of the expressions of this guard expression"
                                                            " are true. This is not allowed, because tasks must be"
                                                            " fully determenistic!"))
                    top.instruction_index = self._edestination
                    return

                else:
                    top.instruction_index = d
                    enabled = True


class Push(Instruction):
    """
    An instruction that pushes a new frame on the stack of the executing task.
    """

    def __init__(self, entry, expressions, destination, edestination):
        """
        Creates a new push instructions.
        :param entry: A Term that evaluates to either a ProgramLocation, a VProcedure, or an IntrinsicProcedure.
        :param expressions: An iterable of Terms that determine the values for the local variables that
                            are to be pushed as part of the stack frame.
        :param destination: The instruction index at which execution should continue after the successful execution of
                            this instruction, as soon as the newly pushed stack frame has been popped again.
        :param edestination: The instruction index at which execution should continue in case this instruction causes
                             an error. Note that any errors caused as long as the newly pushed stack frame still exists
                             will _not_ lead to this error destination! To handle those errors,
                             code reached via 'destination' must explicitly treat them.
        """
        super().__init__()
        self._entry = check_type(entry, Term)
        self._expressions = tuple(check_types(expressions, Term))
        self._destination = check_type(destination, int)
        self._edestination = check_type(edestination, int)

    def __str__(self):
        return "push({}, [{}])".format(self._entry, ", ".join(self._expressions))

    def hash(self):
        return hash((self._entry, self._expressions, self._destination, self._edestination))

    def equals(self, other):
        return isinstance(other, Push) \
               and (self._entry, self._expressions, self._destination, self._edestination) \
               == (other._entry, other._expressions, other._destination, other._edestination)

    def enabled(self, tstate, mstate):
        return True

    def execute(self, tstate, mstate):

        old_top = tstate.stack[-1]

        try:
            location = self._entry.evaluate(tstate, mstate)
            args = tuple(e.evaluate(tstate, mstate) for e in self._expressions)
        except EvaluationException as ee:
            tstate.exception = VException(pexception=ee)
            old_top.instruction_index = self._edestination
            return

        if isinstance(location, VProcedure):
            location = location.entry
        if isinstance(location, ProgramLocation):
            frame = Frame(location.clone_unsealed(), args)
            tstate.push(frame)
            old_top.instruction_index = self._destination
        elif isinstance(location, IntrinsicProcedure):
            location.execute(tstate, mstate, *args)
            old_top.instruction_index = self._destination
        else:
            tstate.exception = VException(pexception=InstructionException("The expression determining the initial program location for the"
                                                    " new stack frame is neither a ProgramLocation nor an Intrinsic function!"))
            old_top.instruction_index = self._edestination


class Pop(Instruction):
    """
    An instruction that pops the top-most frame from the stack.
    """

    def __init__(self):
        super().__init__()

    def __str__(self):
        return "pop"

    def hash(self):
        return 0

    def equals(self, other):
        return isinstance(other, Pop)

    def enabled(self, tstate, mstate):
        return True

    def execute(self, tstate, mstate):
        tstate.pop()


class Launch(Instruction):
    """
    An instruction that launches a new task. This is similar to a push, but pushes to a newly created task stack
    and returns its ID.
    """

    def __init__(self, entry, expressions, destination, edestination):
        """
        Creates a new push instructions.
        :param entry: An Expression that evaluates to either a ProgramLocation or a VProcedure.
        :param expressions: An iterable of Expression objects that determine the values for the local variables that
                            are to be pushed as part of the stack frame.
        :param destination: The instruction index at which execution should continue after the successful execution of
                            this instruction, as soon as the newly pushed stack frame has been popped again.
        :param edestination: The instruction index at which execution should continue in case this instruction causes
                             an error.
        """
        super().__init__()
        self._entry = check_type(entry, Term)
        self._expressions = tuple(check_types(expressions, Term))
        self._destination = check_type(destination, int)
        self._edestination = check_type(edestination, int)

    def hash(self):
        return hash((self._entry, self._expressions, self._destination, self._edestination))

    def equals(self, other):
        return isinstance(other, Launch) \
               and (self._entry, self._expressions, self._destination, self._edestination) \
               == (other._entry, other._expressions, other._destination, other._edestination)

    def enabled(self, tstate, mstate):
        return True

    def execute(self, tstate, mstate):

        mytop = tstate.stack[-1]

        try:
            location = self._entry.evaluate(tstate, mstate)
            args = tuple(e.evaluate(tstate, mstate) for e in self._expressions)
        except EvaluationException as ee:
            tstate.exception = VException(pexception=ee)
            mytop.instruction_index = self._edestination
            return

        if isinstance(location, VProcedure):
            location = location.entry
        if isinstance(location, ProgramLocation):
            frame = Frame(location.clone_unsealed(), args)
            task = StackState(TaskStatus.WAITING, [frame])
            mstate.add_task(task)
            tstate.returned = task
        else:
            tstate.exception = VException(pexception=InstructionException("The expression determining the initial program location for the"
                                                    " new stack frame is not a proper program location!"))
            mytop.instruction_index = self._edestination
            return

        mytop.instruction_index = self._destination


class StackProgram(Immutable):
    """
    An array of stack machine instructions. Each instruction updates the state of a stack machine, in particular
    determining which instruction to execute next.
    """

    def __init__(self, instructions):
        """
        Creates a new stack program.
        :param instructions: An iterable of Instruction objects.
        """
        super().__init__()
        self._instructions = tuple(check_type(i, Instruction) for i in instructions)

    def __str__(self):
        with io.StringIO() as s:
            prefix = "0: "
            for idx, i in enumerate(self._instructions):
                s.write(f"{prefix}{i}")
                prefix = f"\n{idx + 1}: "
            return s.getvalue()

    def hash(self):
        return hash(self._instructions)

    def equals(self, other):
        return isinstance(other, StackProgram) and self._instructions == other._instructions

    def __len__(self):
        return self._instructions

    def __iter__(self):
        return iter(self._instructions)

    def __getitem__(self, item):
        return self._instructions[item]


class ProgramLocation(Immutable, Value):
    """
    A pair of StackProgram and instruction index.
    """

    @property
    def type(self):
        return TBuiltin.location

    def __init__(self, program, index):
        """
        Creates a new program location.
        :param program: The StackProgram this object is pointing into.
        :param index: The index of the instruction in the given stack program that this location is pointing to.
        """
        if not program.sealed:
            raise ValueError("The given program must be sealed!")

        super().__init__()
        self._program = check_type(program, StackProgram)
        self._index = check_type(index, int)

    @property
    def program(self):
        """
        The StackProgram this object is pointing into.
        """
        return self._program

    @property
    def index(self):
        """
        The index of the instruction in the given stack program that this location is pointing to.
        """
        return self._index

    def hash(self):
        check_sealed(self)
        return hash((self._program, self._index))

    def equals(self, other):
        return isinstance(other, ProgramLocation) and (self._program, self._index) == (other._program, other._index)
