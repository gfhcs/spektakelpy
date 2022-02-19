from util import check_type, check_types
from util.immutable import ImmutableEquatable, Sealable, check_sealed, check_unsealed
from .instructions import StackProgram
from ..task import TaskState
from ..task import TaskStatus
from ..values import Value


class Frame(Sealable):
    """
    Represents a set of local variables and a pointer to the next machine instruction to execute.
    """

    def __init__(self, program, instruction_index, local_values):
        """
        Allocates a new stack frame.
        :param program: The machine program to which this stack frame belongs.
        :param instruction_index: The index of the instruction in the given program that is to be executed next.
        :param local_values: The array of values of the local variables stored in this stack frame.
        """
        super().__init__()
        self._program = check_type(program, StackProgram)
        self._location = check_type(instruction_index, int)
        self._local_values = list(check_types(local_values, Value))

    def _seal(self):
        self._local_values = tuple(v.seal() for v in self._local_values)

    def clone_unsealed(self):
        return Frame(self._program, self._location, (v.clone_unsealed() for v in self._local_values))

    def hash(self):
        check_sealed(self)
        return hash((self._program, self._location, self._local_values))

    def equals(self, other):
        return isinstance(other, Frame) and (self._program, self._location) == (other._program, other._location) \
               and len(self._local_values) == len(other._local_values) \
               and all(x == y for x, y in zip(self._local_values, other._local_values))

    @property
    def program(self):
        """
        The machine program to which this stack frame belongs.
        """
        return self._program

    @property
    def instruction_index(self):
        """
        The index of the instruction in the given program that is to be executed next.
        """
        return self._location

    @instruction_index.setter
    def instruction_index(self, value):
        check_unsealed(self)
        self._location = check_type(value, int)

    @property
    def local(self):
        """
        The array of values of the local variables stored in this stack frame.
        """
        return self._local_values


class StackState(TaskState):
    """
    Models the state of a task that executes a control flow graph that may contain function calls.
    """

    def __init__(self, taskid, status, stack, exception=None, returned=None):
        """
        Allocates a new stack state.
        :param taskid: The identity of the task that this object represents a state of.
        :param status: The status of the task, i.e. a TaskStatus object.
        :param stack: A sequence of Frame objects, that, from top to bottom, represent the stack of this task state.
        :param exception: A value that has been raised as an exception and is currently being handled.
        :param returned: A value that is currently being returned from the callee to the caller.
        """
        super().__init__(taskid, status)

        self._stack = list(check_types(stack, Frame))
        self._exception = check_type(exception, Value)
        self._returned = check_type(returned, Value)

    def _seal(self):
        self._stack = tuple(self._stack)
        for f in self._stack:
            f.seal()

    def clone_unsealed(self):
        return StackState(self.taskid, self.status, (f.clone_unsealed() for f in self.stack),
                          exception=self.exception.clone_unsealed(),
                          returned=self.returned.clone_unsealed())

    @property
    def stack(self):
        """
        The sequence of Frame objects, that, from top to bottom, represent the stack of this task state.
        """
        return self._stack

    @property
    def exception(self):
        """
        The value that has been raised as an exception and is currently being handled.
        """
        return self._exception

    @exception.setter
    def exception(self, value):
        check_unsealed(self)
        self._exception = check_type(value, Value)

    @property
    def returned(self):
        """
        The value that is currently being returned from the callee to the caller.
        """
        return self._returned

    @returned.setter
    def returned(self, value):
        check_unsealed(self)
        self._returned = check_type(value, Value)

    def hash(self):
        check_sealed(self)
        return hash((self._stack, self._exception, self._returned))

    def equals(self, other):
        return isinstance(other, StackState) \
               and (self._stack, self._exception, self._returned) == (other._stack, other._exception, other._returned)

    def enabled(self, mstate):
        if len(self.stack) == 0:
            return False
        top = self.stack[0]
        i = top.program[top.instruction_index]
        return i.enabled(self, mstate)

    def run(self, mstate):
        check_unsealed(self)
        tstate = self

        mstate.status = TaskStatus.RUNNING
        progress = False

        # A task is not supposed to yield control unless it really has to.
        # So in order to keep overhead from interleavings low, we just continue execution
        # as long as possible:
        while True:

            if len(tstate.stack) == 0:
                break

            top = tstate.stack[0]

            i = top.program[top.instruction_index]

            if i.enabled(tstate, mstate):
                i.execute(tstate, mstate)
                progress = True
            else:
                if not progress:
                    raise RuntimeError("This task was not enabled and thus should not have been run!")
                tstate.status = TaskStatus.WAITING
                break
