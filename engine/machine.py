from .state import Valuation


class TaskMachine:
    """
    Represents the state of a virtual machine that is executing tasks.
    """

    def __int__(self):
        """
        Creates a new TaskMachine.
        """
        self._tasks = []
        self._valuation = Valuation()

    @property
    def tasks(self):
        """
        The tasks being processed by this TaskMachine.
        """
        return tuple(self._tasks)

    @property
    def valuation(self):
        """
        Maps Variable objects to Value objects.
        """
        return self._valuation.view()

    def write(self, var, val):
        """
        Binds the giving variable to the given value.
        :param var: A Variable object.
        :param val: A Value object.
        """
        self._valuation[var] = val

    def read(self, var):
        """
        Retrieves the value that the given variable is bound to in this TaskMachine.
        :param var: A Variable object.
        :return: A Value object.
        """
        return self._valuation[var]

    def add(self, task):
        """
        Adds the given task to this TaskMachine.
        :param task: The Task object to add.
        :exception ValueError: If the given task already belongs to some TaskMachine.
        """
        if task.machine is not None:
            raise ValueError("The given task already belongs to a TaskMachine!")
        self._tasks.append(task)

    def remove(self, task):
        """
        Removes the given task from the agenda of this TaskMachine.
        :param task: The Task object to remove.
        :exception ValueError: If the given task is not part of this TaskMachine.
        """
        self._tasks.remove(task)


