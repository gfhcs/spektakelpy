from util import check_type, check_types
from util.immutable import Sealable, check_sealed, check_unsealed
from .task import TaskState


class MachineState(Sealable):
    """
    Represents the state of a virtual machine that is executing tasks.
    """

    def __init__(self, heap, task_states):
        """
        Describes the state of the machine.
        :param heap: The heap memory of the machine, i.e. an array of values.
        :param task_states: The states of all the tasks running on the machine.
        """
        super().__init__()
        self._tstates = {check_type(s, TaskState).task_id: s for s in task_states}
        self._heap = list(check_types(heap, Sealable))

    def _seal(self):
        for t in self._tstates.values():
            t.seal()
        self._heap = tuple(self._heap)
        for h in self._heap:
            h.seal()

    def clone_unsealed(self):
        return MachineState((h.clone_unsealed() for h in self._heap),
                            (t.clone_unsealed() for t in self._tstates.values()))

    def hash(self):
        check_sealed(self)
        h = hash(self._heap)
        for s in self._tstates.values():
            h ^= hash(s)
        return h

    def equals(self, other):
        return isinstance(other, MachineState) \
               and tuple(self._heap) == tuple(other._heap) \
               and frozenset(self._tstates.values()) == frozenset(other._tstates.values())

    @property
    def task_states(self):
        """
        The TaskStates for all the tasks running on the machine.
        """
        return self._tstates.values()

    def add_task(self, t):
        """
        Adds a new task to this machine state.
        :param t: The TaskState object to add.
        """
        check_type(t, TaskState)
        check_unsealed(self)
        if t.taskid in self._tstates:
            raise ValueError("A task with ID {} is already part of this machine state!".format(t.taskid))
        self._tstates[t.taskid] = t

    def remove_task(self, tid):
        """
        Removes a task state from this machine state.
        :param tid: The ID of the task state to remove.
        """
        check_unsealed(self)
        del self._tstates[tid]

    @property
    def heap(self):
        """
        The heap memory of the machine.
        """
        return self._heap

    def get_task_state(self, tid):
        """
        Retrieves the state of the specified task.
        :param tid: A task ID object, i.e. an object that one of the TaskState objects records as TaskState.task_id.
        :exception KeyError: If this MachineState object does not record the state of the task with the given task ID.
        :return: One of the TaskState objects recorded in this MachineState object.
        """
        return self._tstates[tid]
