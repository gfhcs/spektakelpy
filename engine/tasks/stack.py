from ..task import TaskState
from util.immutable import ImmutableEquatable
from util import check_type

class Frame(ImmutableEquatable):

    def __init__(self, location, local_values):
        """
        Allocates a new stack frame.
        :param location: A CFG location that the task owning this stack frame is currently resting in.
        :param local_values: The array of values of the local variables stored in this stack frame.
        """
        super().__init__()
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
    Local data can be stored either in a task-local heap, or in a task-local stack.
    """

    def __init__(self):

        self._tasklocal = Valuation()
        self._stack = Stack()

    def enabled(self, mstate):
        # TODO: Check if one of the control flow edges in the location belonging to the top-most stack frame
        #       are enabled. This is done by evaluating their guard expressions.
        pass

    def run(self, mstate):

        # A task is not supposed to yield control unless it really has to.
        # So in order to keep overhead from interleavings low, we just continue execution
        # as long as possible:
        while self.enabled(mstate):
            # TODO: Look at the control location belonging to the top-most stack frame. Make sure exactly one of its
            #       edges is enabled. Follow it.

        #  The task is allocated only if some task actively deallocates it.

        pass

    def hash(self):
        pass

    def equals(self, other):
        pass
