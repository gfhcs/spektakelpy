
import abc
from enum import Enum

from engine.functional import Value
from util import check_type
from util.immutable import check_unsealed


class TaskStatus(Enum):
    """
    Describes the status of a task.
    """
    WAITING = 0    # Task is waiting to begin/resume execution.
    RUNNING = 1    # Task is currently being computed and changing the state.
    COMPLETED = 2  # Task has finished successfully.
    FAILED = 3     # Task has failed.


class TaskState(Value, abc.ABC):
    """
    Represents the current state of a computation.
    """

    @property
    def type(self):
        from engine.functional.types import TBuiltin
        return TBuiltin.task

    def __init__(self, status):
        """
        Creates a new task state.
        :param status: The status of the task, i.e. a TaskStatus object.
        """
        super().__init__()
        self._status = check_type(status, TaskStatus)

    @property
    @abc.abstractmethod
    def rank(self):
        """
        A measure for the priority of this task: If multiple tasks are enabled for execution, those with higher
        rank are preferred. Multiple states may have equal rank. Ranks can change during execution.
        Note to implementers: The rank of a task is part of its state, which means that changing ranks often may
        inflate the state space.
        :return: A number.
        """
        pass

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


class RoundRobinTaskState(TaskState):

    def __init__(self, *largs, **kwargs):
        super().__init__(*largs, **kwargs)
        self._rank = 0

    @property
    def rank(self):
        return self._rank

    @abc.abstractmethod
    def run_before_rank(self, *largs, **kwargs):
        """
        This method implements TaskState.run, but is guaranteed to be followed by a rank update that puts self at
        the end of the rank order of all RoundRobinTask objects in the given mstate.
        """
        pass

    def run(self, mstate):
        self.run_before_rank(mstate)
        for t in mstate.task_states:
            if isinstance(t, RoundRobinTaskState) and t._rank < self._rank:
                t._rank += 1
        self._rank = 0
