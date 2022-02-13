from util import check_type
from util.immutable import ImmutableEquatable
from ..machine import MachineState
from ..task import TaskState
from ..task import TaskStatus


class Frame(ImmutableEquatable):

    def __init__(self, cfg, location, local_values):
        """
        Allocates a new stack frame.
        :param cfg: The control flow graph that this stack frame belongs to.
        :param location: A CFG location that the task owning this stack frame is currently resting in.
        :param local_values: The array of values of the local variables stored in this stack frame.
        """
        super().__init__()
        self._cfg = cfg
        self._location = check_type(location, int)
        self._local_values = tuple(check_type(v, ImmutableEquatable) for v in local_values)

    def hash(self):
        h = hash(self._location)
        for v in self._local_values:
            h ^= v.hash()
        return h

    def equals(self, other):
        return isinstance(other, Frame) \
               and self._location == other._location \
               and len(self._local_values) == len(other._local_values) \
               and all(x == y for x, y in zip(self._local_values, other._local_values))

    @property
    def cfg(self):
        """
        The control flow graph that this stack frame belongs to.
        """
        return self._cfg

    @property
    def location(self):
        """
        A CFG location that the task owning this stack frame is currently resting in.
        """
        return self._location

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

        self._stack = tuple(check_type(f, Frame) for f in stack)
        self._exception = check_type(exception, ImmutableEquatable)
        self._returned = check_type(returned, ImmutableEquatable)

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

    @property
    def returned(self):
        """
        The value that is currently being returned from the callee to the caller.
        """
        return self._returned

    def hash(self):
        return hash(self._stack) ^ hash(self._exception) ^ hash(self._returned)

    def equals(self, other):
        return isinstance(other, StackState) and self._stack == other._stack and self._exception == other._exception and self._returned == other._returned

    def enabled(self, mstate):
        top = self.stack[0]
        for e in top.cfg.edges[top.location]:
            if e.guard.evaluate(self, mstate):
                return True
        return False

    def run(self, mstate):

        tstate = self

        # A task is not supposed to yield control unless it really has to.
        # So in order to keep overhead from interleavings low, we just continue execution
        # as long as possible:
        while True:
            top = tstate.stack[0]
            enabled = None
            for e in top.cfg.edges[top.location]:
                if e.guard.evaluate(tstate, mstate):
                    if enabled is None:
                        enabled = e
                    else:
                        raise RuntimeError("More than one control flow edge of this task is enabled. Such control flow"
                                           " nondeterminism is not supported, because it is not visible to the scheduler"
                                           " and can thus not be taken into account properly!")
            if enabled is None:
                if tstate is self:
                    raise RuntimeError("self.run was called even though self.enabled was not True !")
                else:
                    break

            top_new = Frame(top.cfg, enabled.destination, top.local)
            task_states_new = list(mstate.task_states)
            task_states_new.remove(tstate)
            tstate = StackState(self.taskid, TaskStatus.WAITING, (top_new, *tstate.stack[1:]))
            task_states_new.append(tstate)
            mstate = MachineState(mstate.valuation, task_states=task_states_new)

            for i in enabled.instructions:
                tstate, mstate = i.execute(tstate, mstate)

        #  The task is deallocated only if some task actively deallocates it.

        return mstate
