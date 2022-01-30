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
        self._tstates = {check_type(s, TaskState).task_id: s for s in task_states}
        self._valuation = check_type(valuation, Valuation)
        self._hash = None

    def hash(self):
        if self._hash is None:
            h = hash(self._valuation)
            for s in self._tstates.values():
                h ^= hash(s)
            self._hash = h

        return self._hash

    def equals(self, other):
        if not isinstance(other, MachineState) or other.hash() != self.hash():
            return False
        return self._valuation == other._valuation \
               and frozenset(self._tstates.values()) == frozenset(other._tstates.values())

    @property
    def task_states(self):
        """
        The TaskStates for all the tasks running on the machine.
        """
        return self._tstates.values()

    @property
    def valuation(self):
        """
        The Valuation of the machine.
        """
        return self._valuation

    def get_task_state(self, tid):
        """
        Retrieves the state of the specified task.
        :param tid: A task ID object, i.e. an object that one of the TaskState objects records as TaskState.task_id.
        :exception KeyError: If this MachineState object does not record the state of the task with the given task ID.
        :return: One of the TaskState objects recorded in this MachineState object.
        """
        return self._tstates[tid]
