from engine.core.data import VException, VCancellationError
from engine.core.machine import TaskStatus, TaskState
from engine.core.none import value_none
from engine.core.value import Value
from engine.stack.exceptions import VInstructionException
from engine.stack.frame import Frame
from engine.stack.program import ProgramLocation
from util import check_type, check_types
from util.immutable import check_sealed, check_unsealed


class StackState(TaskState):
    """
    Models the state of a task that executes a control flow graph that may contain function calls.
    """

    def __init__(self, status, stack, exception=None, returned=None):
        """
        Allocates a new stack state.
        :param status: The status of the task, i.e. a TaskStatus object.
        :param stack: A sequence of Frame objects, that, from top to bottom, represent the stack of this task state.
        :param exception: A value that has been raised as an exception and is currently being handled.
        :param returned: A value that is currently being returned from the callee to the caller.
        """
        super().__init__(status)

        self._stack = list(check_types(stack, Frame))
        self._exception = value_none if exception is None else check_type(exception, Value)
        self._returned = value_none if returned is None else check_type(returned, Value)
        self.status = TaskStatus.RUNNING if len(self._stack) > 0 else TaskStatus.COMPLETED

    def cancel(self):
        if self.status in (TaskStatus.CANCELLED, TaskStatus.COMPLETED, TaskStatus.FAILED):
            return
        self.status = TaskStatus.CANCELLED
        self._exception = VCancellationError(True, "Task was cancelled!")

    def dequeue(self, mstate):
        """
        Removes this task from a machine state. This does not invalidate the task, but prevents it from ever
        being scheduled again.
        :param mstate: The MachineState to remove this task from.
        """
        for idx, t in enumerate(mstate.task_states):
            if t is self:
                mstate.remove_task(idx)
                return
        raise ValueError("Could not find the StackState in the given MachineState!")

    def print(self, out):
        out.write("StackState(")
        prefix = ""
        for f in self._stack:
            out.write(prefix)
            ProgramLocation(f.program, f.instruction_index).print(out)
            prefix = ", "
        out.write(")")

    def _seal(self):
        self._stack = tuple(self._stack)
        for f in self._stack:
            f.seal()
        if self._exception is not None:
            self._exception.seal()
        if self._returned is not None:
            self._returned.seal()

    def clone_unsealed(self, clones=None):
        if clones is None:
            clones = {}
        try:
            return clones[id(self)]
        except KeyError:
            c = StackState(self.status, self._stack, self._exception, self._returned)
            clones[id(self)] = c
            c._stack = [f.clone_unsealed(clones=clones) for f in c._stack]
            if c._exception is not None:
                c._exception = c._exception.clone_unsealed(clones=clones)
            if c._returned is not None:
                c._returned = c._returned.clone_unsealed(clones=clones)
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
        return len(self._stack)

    def chash(self):
        return 0

    def bequals(self, other, bijection):
        try:
            return bijection[id(self)] == id(other)
        except KeyError:
            bijection[id(self)] = id(other)
            if not (isinstance(other, StackState)
                    and len(self._stack) == len(other._stack)
                    and self._exception.bequals(other._exception, bijection)
                    and self._returned.bequals(other._returned, bijection)):
                return False
            return all(a.bequals(b, bijection) for a, b in zip(self._stack, other._stack))

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

        if tstate.status != TaskStatus.CANCELLED:
            tstate.status = TaskStatus.RUNNING
        progress = False

        # A task is not supposed to yield control unless it really has to.
        # So in order to keep overhead from interleavings low, we just continue execution
        # as long as possible:
        while True:

            if len(tstate.stack) == 0:
                if tstate.status != TaskStatus.CANCELLED:
                    tstate.status = TaskStatus.FAILED if isinstance(self.exception, VException) else TaskStatus.COMPLETED
                self.dequeue(mstate)
                break

            top = tstate.stack[-1]

            try:
                i = top.program[top.instruction_index]
            except IndexError:
                self.exception = VInstructionException("Instruction index invalid, don't know how to continue.")
                tstate.status = TaskStatus.FAILED
                self.dequeue(mstate)
                break

            if i.enabled(tstate, mstate):
                i.execute(tstate, mstate)
                progress = True
            else:
                if not progress:
                    raise RuntimeError("This task was not enabled and thus should not have been run!")
                if tstate.status != TaskStatus.CANCELLED:
                    tstate.status = TaskStatus.WAITING
                break

