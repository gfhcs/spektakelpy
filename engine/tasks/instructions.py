import abc


class Instruction(abc.ABC):
    """
    Models the smallest, atomic execution steps.
    """

    @abc.abstractmethod
    def execute(self, tstate, mstate):
        """
        Executes this instruction in the given state.
        :param tstate: The task state that this instruction is to be executed in. It must be part of the given machine
        state. Any references to task-local variables will be interpreted with respect to this task state.
        :param mstate: The machine state that this instruction is to be executed in. It must contain the given task
        state.
        :return: A new pair tstate, mstate that represents the result of executing this instruction.
        """
        pass
