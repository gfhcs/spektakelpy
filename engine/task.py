
import abc
from enum import Enum

from engine.functional import Value
from engine.intrinsic import IntrinsicInstanceMethod
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
    CANCELLED = 4  # Task has been cancelled.


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

    @IntrinsicInstanceMethod
    @abc.abstractmethod
    def cancel(self):
        raise NotImplementedError()

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

