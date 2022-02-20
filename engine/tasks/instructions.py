import abc

from util import check_type, check_types
from util.immutable import Immutable, Sealable, check_unsealed, check_sealed
from .expressions import EvaluationException, Expression
from .reference import Reference
from .stack import Frame, StackState
from ..task import TaskStatus


class InstructionException(Exception):
    # TODO: This must be a value!
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

    def __init__(self, ref, expression, destination, edestination):
        """
        Creates a new update instruction.
        :param ref: An Expression specifying which part of the state is to be updated.
        :param expression: The Expression object specifying how to compute the new value.
        :param destination: The index of the instruction that is to be executed after this one.
        :param edestination: The index of the instruction to jump to if this instruction causes an error.
        """
        super().__init__()
        self._ref = check_type(ref, Expression)
        self._expression = check_type(expression, Expression)
        self._destination = check_type(destination, int)
        self._edestination = check_type(edestination, int)

    def enabled(self, tstate, mstate):
        return True

    def hash(self):
        return hash((self._ref, self._expression, self._destination, self._edestination))

    def equals(self, other):
        return isinstance(other, Update) \
               and (self._ref, self._expression, self._destination, self._edestination) \
               == (other._ref, other._expression, other._destination, other._edestination)

    @property
    def reference(self):
        """
        The Expression object specifying which part of the state is to be updated.
        """
        return self._ref

    @property
    def expression(self):
        """
        The expression object specifying how to compute the new value.
        """
        return self._expression

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
            value = self._expression.evaluate(tstate, mstate)
        except EvaluationException as ee:
            tstate.exception = ee
            top.instruction_index = self._edestination
            return

        if not isinstance(ref, Reference):
            tstate.exception = InstructionException("The expression determining what part of the state to update did "
                                                    "not evaluate to a proper reference!")
            top.instruction_index = self._edestination
            return
        ref.write(tstate, mstate, value)


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
        self._alternatives = {check_type(e, Expression): check_type(d, int) for e, d in alternatives.items()}
        self._edestination = check_type(edestination, int)

    @property
    def expressions(self):
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
        try:
            return any(bool(e.evaluate(tstate, mstate)) for e in self._alternatives.keys())
        except EvaluationException:
            return True

    def execute(self, tstate, mstate):

        enabled = False

        top = tstate.stack[-1]

        for e, d in self._alternatives.items():

            try:
                r = bool(e.evaluate(tstate, mstate))
            except EvaluationException as ee:
                tstate.exception = ee
                top.instruction_index = self._edestination
                return

            if r:
                if enabled:
                    tstate.exception = InstructionException("More than one of the expressions of this guard expression"
                                                            " are true. This is not allowed, because tasks must be"
                                                            " fully determenistic!")
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
        :param entry: An Expression that evaluates to a ProgramLocation.
        :param expressions: An iterable of Expression objects that determine the values for the local variables that
                            are to be pushed as part of the stack frame.
        :param destination: The instruction index at which execution should continue after the successful execution of
                            this instruction, as soon as the newly pushed stack frame has been popped again.
        :param edestination: The instruction index at which execution should continue in case this instruction causes
                             an error. Note that any errors caused as long as the newly pushed stack frame still exists
                             will _not_ lead to this error destination! To handle those errors,
                             code reached via 'destination' must explicitly treat them.
        """
        super().__init__()
        self._entry = check_type(entry, Expression)
        self._expressions = tuple(check_types(expressions, Expression))
        self._destination = check_type(destination, int)
        self._edestination = check_type(edestination, int)

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
            tstate.exception = ee
            old_top.instruction_index = self._edestination
            return

        try:
            check_type(location, ProgramLocation)
        except AssertionError:
            tstate.exception = InstructionException("The expression determining the initial program location for the"
                                                    " new stack frame is not a proper program location!")
            old_top.instruction_index = self._edestination
            return

        frame = Frame(location, args)
        tstate.stack.append(frame)
        old_top.instruction_index = self._destination


class Pop(Instruction):
    """
    An instruction that pops the top-most frame from the stack.
    """

    def __init__(self):
        super().__init__()

    def hash(self):
        return 0

    def equals(self, other):
        return isinstance(other, Pop)

    def enabled(self, tstate, mstate):
        return True

    def execute(self, tstate, mstate):
        tstate.stack.pop()


class Launch(Instruction):
    """
    An instruction that launches a new task. This is similar to a push, but pushes to a newly created task stack
    and returns its ID.
    """

    def __init__(self, entry, expressions, destination, edestination):
        """
        Creates a new push instructions.
        :param entry: An Expression that evaluates to a ProgramLocation.
        :param expressions: An iterable of Expression objects that determine the values for the local variables that
                            are to be pushed as part of the stack frame.
        :param destination: The instruction index at which execution should continue after the successful execution of
                            this instruction, as soon as the newly pushed stack frame has been popped again.
        :param edestination: The instruction index at which execution should continue in case this instruction causes
                             an error. Note that any errors caused as long as the newly pushed stack frame still exists
                             will _not_ lead to this error destination! To handle those errors,
                             code reached via 'destination' must explicitly treat them.
        """
        super().__init__()
        self._entry = check_type(entry, Expression)
        self._expressions = tuple(check_types(expressions, Expression))
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
            tstate.exception = ee
            mytop.instruction_index = self._edestination
            return

        try:
            check_type(location, ProgramLocation)
        except AssertionError:
            tstate.exception = InstructionException("The expression determining the initial program location for the"
                                                    " new stack frame is not a proper program location!")
            mytop.instruction_index = self._edestination
            return

        frame = Frame(location, args)

        tids = set(t.tid for t in mstate.task_states)
        tid = None
        for tid in range(len(tids) + 1):
            if tid not in tids:
                break

        assert tid is not None and tid not in tids
        mstate.add_task(StackState(tid, TaskStatus.WAITING, [frame]))
        tstate.returned = tid
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


class ProgramLocation(Sealable):
    """
    A pair of StackProgram and instruction index.
    """

    def __init__(self, program, index):
        """
        Creates a new program location.
        :param program: The StackProgram this object is pointing into.
        :param index: The index of the instruction in the given stack program that this location is pointing to.
        """
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

    @index.setter
    def index(self, value):
        check_unsealed(self)
        self._index = check_type(value, int)

    def hash(self):
        check_sealed(self)
        return hash((self._program, self._index))

    def equals(self, other):
        return isinstance(other, ProgramLocation) and (self._program, self._index) == (other._program, other._index)

    def _seal(self):
        pass

    def clone_unsealed(self):
        return ProgramLocation(self._program, self._index)
