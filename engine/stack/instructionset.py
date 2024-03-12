from engine.core.exceptions import VException, VCancellationError
from engine.core.machine import TaskStatus
from engine.core.none import VNone
from engine.core.procedure import Procedure
from engine.stack.exceptions import VTypeError, VInstructionException
from engine.stack.instruction import Instruction
from engine.stack.state import StackState
from engine.stack.term import Term
from util import check_type, check_types


def pack_exception(e, msg=None):
    """
    Wraps Python exceptions in VExceptions, but forwards VExceptions unmodified.
    :param e: The Exception object to (potentially) wrap.
    :param msg: The message to use for the VException, unless e is already a VException.
    :return: A VException object.
    """
    return e if isinstance(e, VException) else VException(str(e) if msg is None else msg, pexception=e)


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

    def print(self, out):
        Update.print_proto(out, self._ref, self._term, self._edestination)

    @staticmethod
    def print_proto(out, ref, term, on_error):
        ref.print(out)
        out.write(" := ")
        term.print(out)
        out.write(f"\ton_error: {on_error}")

    def enabled(self, tstate, mstate):
        return True

    def hash(self):
        return -1

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

        if isinstance(tstate.exception, VCancellationError) and tstate.exception.initial:
            tstate.exception = VCancellationError(False, "Task was cancelled!")
            top.instruction_index = self._edestination
            return

        try:
            ref = self._ref.evaluate(tstate, mstate)
            value = self._term.evaluate(tstate, mstate)
        except Exception as e:
            tstate.exception = pack_exception(e, msg="Failed to evaluate expression")
            top.instruction_index = self._edestination
            return

        try:
            ref.write(tstate, mstate, value)
        except Exception as e:
            tstate.exception = pack_exception(e, msg="Failed to write to reference!")
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

    def print(self, out):
        Guard.print_proto(out, self._alternatives, self._edestination)

    @staticmethod
    def print_proto(out, alternatives, on_error):
        out.write("guard {")
        prefix = ""
        for t, d in alternatives.items():
            out.write(prefix)
            t.print(out)
            out.write(f": {d}")
            prefix = ", "
        out.write(f"}}\ton_error: {on_error}")

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
        return len(self._alternatives)

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
            return (isinstance(tstate.exception, VCancellationError) and tstate.exception.initial or
                    any(e.evaluate(tstate, mstate).value for e in self._alternatives.keys()))
        except VException:
            # If the enabledness check fails, we want to make the error surface, but we are not allowed to change
            # state. This is why we instead return True, such that the instruction can be executed, leading to the
            # enabledness check failing a second time, in a context in which state *can* be changed.
            return True

    def execute(self, tstate, mstate):

        top = tstate.stack[-1]

        if isinstance(tstate.exception, VCancellationError) and tstate.exception.initial:
            tstate.exception = VCancellationError(False, "Task was cancelled!")
            top.instruction_index = self._edestination
            return

        enabled = False
        for e, d in self._alternatives.items():

            try:
                r = bool(e.evaluate(tstate, mstate))
            except Exception as e:
                tstate.exception = pack_exception(e, msg="Failed to evaluate expression!")
                top.instruction_index = self._edestination
                return

            if r:
                if enabled:
                    tstate.exception = VInstructionException("More than one of the expressions of this guard expression"
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

    def __init__(self, callee, terms, destination, edestination):
        """
        Creates a new push instructions.
        :param callee: A Term that evaluates to a callable object.
                      A callable object is either a ProgramLocation, a VProcedure, an IntrinsicProcedure,
                      or a type.
        :param terms: An iterable of Terms that determine the values for the local variables that
                            are to be pushed as part of the stack frame.
        :param destination: The instruction index at which execution should continue after the successful execution of
                            this instruction, as soon as the newly pushed stack frame has been popped again.
        :param edestination: The instruction index at which execution should continue in case this instruction causes
                             an error. Note that any errors caused as long as the newly pushed stack frame still exists
                             will _not_ lead to this error destination! To handle those errors,
                             code reached via 'destination' must explicitly treat them.
        """
        super().__init__()
        self._callee = check_type(callee, Term)
        self._aterms = tuple(check_types(terms, Term))
        self._destination = check_type(destination, int)
        self._edestination = check_type(edestination, int)

    def print(self, out):
        Push.print_proto(out, self._callee, self._aterms, self._edestination)

    @staticmethod
    def print_proto(out, callee, aexpressions, on_error):
        out.write("push(")
        callee.print(out)
        out.write(", [")
        prefix = ""
        for e in aexpressions:
            out.write(prefix)
            e.print(out)
            prefix = ", "
        out.write(f"])\ton_error: {on_error}")

    def hash(self):
        return -2

    def equals(self, other):
        return isinstance(other, Push) \
               and (self._callee, self._aterms, self._destination, self._edestination) \
               == (other._callee, other._aterms, other._destination, other._edestination)

    def enabled(self, tstate, mstate):
        return True

    def execute(self, tstate, mstate):

        old_top = tstate.stack[-1]

        if isinstance(tstate.exception, VCancellationError) and tstate.exception.initial:
            tstate.exception = VCancellationError(False, "Task was cancelled!")
            old_top.instruction_index = self._edestination
            return

        try:
            callee = self._callee.evaluate(tstate, mstate)
            args = tuple(e.evaluate(tstate, mstate) for e in self._aterms)
        except Exception as e:
            tstate.exception = pack_exception(e, msg="Failed to evaluate expression!")
            old_top.instruction_index = self._edestination
            return

        if not isinstance(callee, Procedure):
            tstate.exception = VTypeError("The callee term did not evaluate to a callable procedure!")
            old_top.instruction_index = self._edestination
            return

        try:
            r = callee.initiate(tstate, mstate, *args)
            tstate.returned = VNone.instance if r is None else r
        except Exception as e:
            tstate.exception = pack_exception(e, msg="Failed to call procedure!")
            old_top.instruction_index = self._edestination
        else:
            old_top.instruction_index = self._destination


class Pop(Instruction):
    """
    An instruction that pops the top-most frame from the stack.
    """

    def __init__(self, edestination):
        """
        :param edestination: The instruction index at which execution should continue in case this instruction causes
                     an error.
        """
        super().__init__()
        self._edestination = check_type(edestination, int)

    def print(self, out):
        Pop.print_proto(out)

    @staticmethod
    def print_proto(out):
        out.write("pop")

    def hash(self):
        return -3

    def equals(self, other):
        return isinstance(other, Pop)

    def enabled(self, tstate, mstate):
        return True

    def execute(self, tstate, mstate):
        if isinstance(tstate.exception, VCancellationError) and tstate.exception.initial:
            tstate.exception = VCancellationError(False, "Task was cancelled!")
            tstate.stack[-1].instruction_index = self._edestination
            return
        tstate.pop()


class Launch(Instruction):
    """
    An instruction that launches a new task. This is similar to a push, but pushes to a newly created task stack
    and returns its ID.
    """

    def __init__(self, callee, terms, destination, edestination):
        """
        Creates a new push instructions.
        :param callee: An Expression that evaluates to either a ProgramLocation or a VProcedure.
        :param terms: An iterable of Expression objects that determine the values for the local variables that
                            are to be pushed as part of the stack frame.
        :param destination: The instruction index at which execution should continue after the successful execution of
                            this instruction, as soon as the newly pushed stack frame has been popped again.
        :param edestination: The instruction index at which execution should continue in case this instruction causes
                             an error.
        """
        super().__init__()
        self._callee = check_type(callee, Term)
        self._aterms = tuple(check_types(terms, Term))
        self._destination = check_type(destination, int)
        self._edestination = check_type(edestination, int)

    def print(self, out):
        Launch.print_proto(out, self._callee, self._aterms, self._edestination)

    @staticmethod
    def print_proto(out, callee, aexpressions, on_error):
        out.write("launch(")
        callee.print(out)
        out.write(", [")
        prefix = ""
        for e in aexpressions:
            out.write(prefix)
            e.print(out)
            prefix = ", "
        out.write(f"])\ton_error: {on_error}")

    def hash(self):
        return -4

    def equals(self, other):
        return isinstance(other, Launch) \
               and (self._callee, self._aterms, self._destination, self._edestination) \
               == (other._callee, other._aterms, other._destination, other._edestination)

    def enabled(self, tstate, mstate):
        return True

    def execute(self, tstate, mstate):

        mytop = tstate.stack[-1]

        if isinstance(tstate.exception, VCancellationError) and tstate.exception.initial:
            tstate.exception = VCancellationError(False, "Task was cancelled!")
            mytop.instruction_index = self._edestination
            return

        try:
            callee = self._callee.evaluate(tstate, mstate)
            args = tuple(e.evaluate(tstate, mstate) for e in self._aterms)
        except Exception as e:
            tstate.exception = pack_exception(e, msg="Failed to evaluate expression!")
            mytop.instruction_index = self._edestination
            return

        if not isinstance(callee, Procedure):
            tstate.exception = VTypeError("The callee term did not evaluate to a callable procedure!")
            mytop.instruction_index = self._edestination
            return

        task = StackState(TaskStatus.WAITING, [])
        mstate.add_task(task)
        tstate.returned = task
        try:
            r = callee.initiate(task, mstate, *args)
            task.returned = VNone.instance if r is None else r
        except Exception as e:
            tstate.exception = pack_exception(e, msg="Failed to call procedure!")
            mytop.instruction_index = self._edestination
        else:
            mytop.instruction_index = self._destination




