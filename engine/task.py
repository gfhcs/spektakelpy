
import abc
from enum import Enum


class TaskStatus(Enum):
    """
    Describes the status of a task.
    """
    SCHEDULED = 0  # Task is scheduled for execution on a TaskMachine, but inactive.
    ACTIVE = 1  # Task is being executed.
    WAITING = 2  # Task execution is been interrupted, task is waiting to resume execution.
    COMPLETED = 3  # Task has finished execution successfully.
    FAILED = 4  # Task execution has failed.


class Task(abc.ABC):
    """
    Represents a computation that is currently in the process of being executed by a TaskMachine.
    """

    def __init__(self, m):
        """
        Creates a new task and adds it to the given TaskMachine.
        :param m: The TaskMachine that this task is created for and to which it is added by this constructor.
        """
        super().__init__()

        self._machine = None
        self._status = TaskStatus.SCHEDULED

        m.add(self)
        self._machine = m

    @property
    def status(self):
        """
        The status of this task.
        """
        return self._status

    @abc.abstractmethod
    def decide_guard(self):
        """
        Decides whether this task can continue its execution in the current state of the task machine it belongs to.
        This procedure does not change the state of the TaskMachine or any of its tasks.
        :return: A boolean value.
        """

    @abc.abstractmethod
    def execute(self):
        """
        Progresses in the execution of this task, until the task either terminates, or yields control.
        This procedure advances the state of its TaskMachine.
        :exception RuntimeError: If self.decide_guard does not return True at the time this method is called.
        """
        pass