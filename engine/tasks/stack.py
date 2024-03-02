from engine.functional.values import VException, VNone, VCancellationError
from util import check_type, check_types
from util.immutable import Sealable, check_sealed, check_unsealed
from util.printable import Printable
from .program import ProgramLocation
from ..functional import Value
from ..task import TaskState, TaskStatus


class Frame(Value):
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

    @property
    def type(self):
        raise NotImplementedError("Stack frames and their types are supposed to not be visible for machine programs!")

    def __len__(self):
        return len(self._local_values)

    def resize(self, new_length):
        """
        Changes the number of local variables in this stack frame.
        :param new_length: The new number of local variables in this stack frame.
        """
        d = new_length - len(self._local_values)
        if d > 0:
            from engine.functional.values import VNone

            self._local_values.extend([VNone.instance] * d)
        elif d < 0:
            self._local_values = self._local_values[:d]

    def print(self, out):
        out.write("Frame@")
        self._location.print(out)
        out.write(": [")
        prefix = ""
        for v in self._local_values:
            out.write(prefix)
            v.print(out)
            prefix = ", "
        out.write("]")

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
            c = Frame(self._location, self._local_values)
            clones[id(self)] = c
            c._location = c._location.clone_unsealed(clones)
            c._local_values = [v.clone_unsealed(clones=clones) for v in c._local_values]
            return c

    def hash(self):
        check_sealed(self)
        return len(self._local_values)

    def bequals(self, other, bijection):
        try:
            return bijection[id(self)] == id(other)
        except KeyError:
            bijection[id(self)] = id(other)
            if not (isinstance(other, Frame)
                    and len(self._local_values) == len(other._local_values)
                    and self._location.bequals(other._location, bijection)):
                return False
            return all(a.bequals(b, bijection) for a, b in zip(self._local_values, other._local_values))

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
        from .instructions import ProgramLocation
        check_unsealed(self)
        self._location = ProgramLocation(self._location.program, value)

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
        self._local_values[index] = check_type(value, Value)

    def __getitem__(self, index):
        return self.local[index]

    def __setitem__(self, index, value):
        self.set_local(index, value)


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
        self._exception = VNone.instance if exception is None else check_type(exception, Value)
        self._returned = VNone.instance if exception is None else check_type(returned, Value)
        self.status = TaskStatus.RUNNING if len(self._stack) > 0 else TaskStatus.COMPLETED

    def cancel(self):
        if self.status in (TaskStatus.CANCELLED, TaskStatus.COMPLETED, TaskStatus.FAILED):
            return
        self.status = TaskStatus.CANCELLED
        self._exception = VCancellationError(True)

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
                from . import InstructionException
                self.exception = VException("Failed to execute instruction!", pexception=InstructionException("Instruction index invalid, don't know how to continue."))
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

