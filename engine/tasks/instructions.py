import abc

from .reference import Reference
from .expressions import Expression


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
        :return: A new MachineState object that represents the result of executing this instruction.
        """
        pass


class UpdateInstruction(Instruction):
    """
    An instruction that updates the contents of a memory location.
    """

    def __init__(self, address, expression):
        """
        Creates a new update instruction.
        :param address: The Address object specifying which part of the state is to be updated.
        :param expression: The expression object specifying how to compute the new value.
        """
        super().__init__()
        self._address = check_type(address, Reference)
        self._expression = check_type(expression, Expression)

    @property
    def address(self):
        """
        The Address object specifying which part of the state is to be updated.
        """
        return self._address

    @property
    def expression(self):
        """
        The expression object specifying how to compute the new value.
        """
        return self._expression

    def execute(self, tstate, mstate):
        value = self._expression.evaluate(tstate, mstate)
        return self._address.write(mstate, value)

