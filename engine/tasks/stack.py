from util import check_type, check_types
from util.immutable import Sealable, check_sealed, check_unsealed
from ..task import TaskState
from ..task import TaskStatus
from engine.functional.values import Value, VException


class Frame(Sealable):
    """
    Represents a set of local variables and a pointer to the next machine instruction to execute.
    """

    def __init__(self, location, local_values):
        """
        Allocates a new stack frame.
        :param location: The program location of the instruction that is to be executed next.
        :param local_values: The array of values of the local variables stored in this stack frame.
        """
        super().__init__()
        from .instructions import ProgramLocation

        self._location = check_type(location, ProgramLocation)
        self._local_values = list(check_types(local_values, Value))

    def _seal(self):
        self._location.seal()
        for v in self._local_values:
            v.seal()
        self._local_values = tuple(self._local_values)

    def clone_unsealed(self, clones=None):
        if clones is None:
            clones = {}
        try:
            return clones[id(self)]
        except KeyError:
            c = Frame(self._location.clone_unsealed(clones), (v.clone_unsealed(clones=clones) for v in self._local_values))
            clones[id(self)] = c
            return c

    def hash(self):
        check_sealed(self)
        return hash((self._location, self._local_values))

    def equals(self, other):
        return isinstance(other, Frame) and self._location == other._location \
               and len(self._local_values) == len(other._local_values) \
               and all(x == y for x, y in zip(self._local_values, other._local_values))

    @property
    def program(self):
        """
        The machine program to which this stack frame belongs.
        """
        return self._location.program

    @property
    def instruction_index(self):
        """
        The index of the instruction in the given program that is to be executed next.
        """
        return self._location.index

    @instruction_index.setter
    def instruction_index(self, value):
        check_unsealed(self)
        self._location.index = value

    @property
    def local(self):
        """
        The array of values of the local variables stored in this stack frame.
        """
        return tuple(self._local_values)

    def set_local(self, index, value):
        """
        Updates a local variable recorded in this frame.
        :param index: The index of the local variable to update.
        :param value: The new value for the local variable.
        """
        check_unsealed(self)
        self._local_values[index] = value

    def __getitem__(self, index):
        return self.local[index]

    def __setitem__(self, index, value):
        self.set_local(index, value)


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
        self._exception = check_type(exception, Value, allow_none=True)
        self._returned = check_type(returned, Value, allow_none=True)

    def _seal(self):
        self._stack = tuple(self._stack)
        for f in self._stack:
            f.seal()

    def clone_unsealed(self, clones=None):
        if clones is None:
            clones = {}
        try:
            return clones[id(self)]
        except KeyError:
            c = StackState(self.taskid, self.status, [f.clone_unsealed(clones=clones) for f in self.stack],
                           exception=None if self.exception is None else self.exception.clone_unsealed(clones=clones),
                           returned=None if self.returned is None else self.returned.clone_unsealed(clones=clones))
            clones[id(self)] = c
            return c

    @property
    def stack(self):
        """
        The sequence of Frame objects, that, from top to bottom, represent the stack of this task state.
        """
        return tuple(self._stack)

    def push(self, frame):
        """
        Pushes a frame onto the stack of this StackState.
        :param frame: The Frame object to push onto the stack.
        """
        self._stack.append(check_type(frame, Frame))

    def pop(self):
        """
        Pops a frame from the top of the stack.
        :return: The Frame that was popped.
        """
        return self._stack.pop(-1)

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
        top = self.stack[-1]
        try:
            i = top.program[top.instruction_index]
        except IndexError:
            return False
        return i.enabled(self, mstate)

    def run(self, mstate):
        check_unsealed(self)
        tstate = self

        tstate.status = TaskStatus.RUNNING
        progress = False

        # A task is not supposed to yield control unless it really has to.
        # So in order to keep overhead from interleavings low, we just continue execution
        # as long as possible:
        while True:

            if len(tstate.stack) == 0:
                break

            top = tstate.stack[-1]

            try:
                i = top.program[top.instruction_index]
            except IndexError:
                from .instructions import InstructionException
                self.exception = VException(pexception=InstructionException("Instruction index invalid, don't know how to continue."))
                tstate.status = TaskStatus.FAILED
                break

            if i.enabled(tstate, mstate):
                i.execute(tstate, mstate)
                progress = True
            else:
                if not progress:
                    raise RuntimeError("This task was not enabled and thus should not have been run!")
                tstate.status = TaskStatus.WAITING
                break

