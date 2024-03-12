import abc
from enum import Enum

from engine.core.atomic import type_object
from engine.core.intrinsic import intrinsic
from engine.core.value import Value
from util import check_type, check_types
from util.immutable import check_unsealed, check_sealed


class TaskStatus(Enum):
    """
    Describes the status of a task.
    """
    WAITING = 0    # Task is waiting to begin/resume execution.
    RUNNING = 1    # Task is currently being computed and changing the state.
    COMPLETED = 2  # Task has finished successfully.
    FAILED = 3     # Task has failed.
    CANCELLED = 4  # Task has been cancelled.


@intrinsic("task", [type_object])
class TaskState(Value, abc.ABC):
    """
    Represents the current state of a computation.
    """

    @property
    def type(self):
        return TaskState.intrinsic_type

    def __init__(self, status):
        """
        Creates a new task state.
        :param status: The status of the task, i.e. a TaskStatus object.
        """
        super().__init__()
        self._status = check_type(status, TaskStatus)

    @intrinsic()
    @abc.abstractmethod
    def cancel(self):
        """
        Sets the status of this task to 'CANCELLED' and prevents the task from ever reaching completion.
        The task may still be scheduled!
        """
        if self.cancel is TaskState.cancel:
            raise NotImplementedError("This procedure must be overriden by subclasses!")
        return self.cancel()

    @property
    def status(self):
        """
        The status of this task.
        """
        return self._status

    @status.setter
    def status(self, value):
        check_unsealed(self)
        self._status = check_type(value, TaskStatus)

    def equals(self, other):
        return self is other

    def cequals(self, other):
        return self.equals(other)

    @abc.abstractmethod
    def enabled(self, mstate):
        """
        Indicates whether this task can continue its execution in the current machine state.
        :param mstate: A MachineState object based on which enabledness is to be decided.
        :return: A boolean value.
        """
        pass

    @abc.abstractmethod
    def run(self, mstate):
        """
        Progresses in the execution of this task, until the task either terminates, or yields control.
        This procedure may modify the given mstate object.
        :param mstate: An unsealed MachineState object that is to be modified to become the result of running this task.
        :exception RuntimeError: If self.enabled is not True when this method is called.
        """
        pass


class MachineState(Value):
    """
    Represents the state of a virtual machine that is executing tasks.
    """

    @property
    def type(self):
        raise NotImplementedError("MachineStates should be visible for machine programs!")

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
        # According to the documentation of Value.bequals, Value.equals is supposed to decide
        # "if a machine program can possibly tell self apart from other". For the case of MachineState objects this
        # is equivalent to the semantics of Value.bequals.
        return self.bequals(other, {})

    def bequals(self, other, bijection):
        try:
            return bijection[id(self)] == id(other)
        except KeyError:
            bijection[id(self)] = id(other)
            if not (isinstance(other, MachineState)
                    and len(self._tstates) == len(other._tstates)):
                return False
            return all(a.bequals(b, bijection) for a, b in zip(self._tstates, other._tstates))

    def cequals(self, other):
        # This should actually never be called, because machine programs don't have access to the entire machine state.
        return self.equals(other)

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
