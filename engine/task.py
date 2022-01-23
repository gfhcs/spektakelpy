
import abc
from enum import Enum


class TaskStatus(Enum):
    """
    Describes the status of a task.
    """
    SCHEDULED = 0  # Task is scheduled for execution on a TaskMachine, but inactive.
    ACTIVE = 1  # Task is being executed.
    COMPLETED = 2  # Task has finished execution successfully.
    FAILED = 3  # Task execution has failed.


class Task(abc.ABC):

    def __init__(self, m, awaited):
        super().__init__()
        # TODO: Add self to task machine!

        self._awaited = awaited
        self._status = TaskStatus.SCHEDULED

    @property
    def awaited(self):
        """
        The tasks that need to be completed succesfully before this task can be executed.
        """
        return self._awaited

    @property
    def status(self):
        """
        The status of this task.
        """
        return self._status

    @abc.abstractmethod
    def execute(self):
        # TODO: Check if dependencies are alive!
        # TODO: Remove from agenda!
        pass