from util import check_type, check_types
from util.immutable import Sealable, check_sealed, check_unsealed
from util.printable import Printable
from .task import TaskState


class MachineState(Printable, Sealable):
    """
    Represents the state of a virtual machine that is executing tasks.
    """

    def __init__(self, task_states):
        """
        Describes the state of the machine.
        :param task_states: The states of all the tasks running on the machine.
        """
        super().__init__()
        self._tstates = check_types(task_states, TaskState)

    def print(self, out):
        out.write("MachineState(")
        prefix = ""
        for t in self._tstates:
            out.write(prefix)
            t.print(out)
            prefix = ", "
        out.write(")")

    def _seal(self):
        for t in self._tstates:
            t.seal()
        self._tstates = tuple(self._tstates)

    def clone_unsealed(self, clones=None):
        if clones is None:
            clones = {}
        try:
            return clones[id(self)]
        except KeyError:
            c = MachineState((t.clone_unsealed(clones=clones) for t in self._tstates))
            clones[id(self)] = c
            return c

    def hash(self):
        check_sealed(self)
        h = 4711
        for s in self._tstates:
            h ^= hash(s)
        return h

    def equals(self, other):
        return isinstance(other, MachineState) \
               and frozenset(self._tstates) == frozenset(other._tstates)

    @property
    def task_states(self):
        """
        The TaskStates for all the tasks running on the machine.
        """
        return tuple(self._tstates)

    def add_task(self, t, index=None):
        """
        Adds a new task to this machine state.
        :param t: The TaskState object to add.
        :param index: The index at which the new stask is to be added.
        """
        check_unsealed(self)
        t = check_type(t, TaskState)
        if index is None:
            self._tstates.append(t)
        else:
            self._tstates.insert(index, t)

    def remove_task(self, idx):
        """
        Removes a task state from this machine state.
        :param idx: The index of the task to remove.
        """
        check_unsealed(self)
        del self._tstates[idx]

