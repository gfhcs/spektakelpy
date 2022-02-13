
import abc
from enum import Enum
from util.immutable import ImmutableEquatable


class TaskStatus(Enum):
    """
    Describes the status of a task.
    """
    WAITING = 0    # Task is waiting to begin/resume execution.
    RUNNING = 1    # Task is currently being computed and changing the state.
    COMPLETED = 2  # Task has finished successfully.
    FAILED = 3     # Task has failed.


class TaskState(abc.ABC, ImmutableEquatable):
    """
    Represents the current state of a computation.
    """

    def __init__(self, taskid, status):
        """
        Creates a new task state.
        :param taskid: The identity of the task that this object represents a state of.
        :param status: The status of the task, i.e. a TaskStatus object.
        """
        super().__init__()
        self._taskid = taskid
        self._status = status

    @property
    def taskid(self):
        """
        The identity of the task that this object represents a state of.
        :return: An object.
        """
        return self._taskid

    @property
    def status(self):
        """
        The status of this task.
        """
        return self._status

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
        :param mstate: A MachineState object based on which the result of running this task is to be computed.
        :exception RuntimeError: If self.enabled is not True when this method is called.
        :return: A MachineState object that represents the result of running this task until it yields control again.
        """
        pass
