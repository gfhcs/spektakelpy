from .state import Valuation
from util import check_type
from .task import TaskState
from util.immutable import ImmutableEquatable


class MachineState(ImmutableEquatable):
    """
    Represents the state of a virtual machine that is executing tasks.
    """

    def __init__(self, valuation, task_states):
        """
        Describes the state of the machine.
        :param valuation: The valuation of the machine.
        :param task_states: The states of all the tasks running on the machine.
        """
        super().__init__()
        self._tstates = frozenset(check_type(s, TaskState) for s in task_states)
        self._valuation = check_type(valuation, Valuation)
        self._hash = None

    def hash(self):
        if self._hash is None:
            h = hash(self._valuation)
            for s in self._tstates:
                h ^= hash(s)
            self._hash = h

        return self._hash

    def equals(self, other):
        if not isinstance(other, MachineState) or other.hash() != self.hash():
            return False
        return self._valuation == other._valuation and self._tstates == other._tstates

    @property
    def task_states(self):
        """
        The TaskStates for all the tasks running on the machine.
        """
        return self._tstates

    @property
    def valuation(self):
        """
        The Valuation of the machine.
        """
        return self._valuation

