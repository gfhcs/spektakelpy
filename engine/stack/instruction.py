import abc

from util.immutable import Immutable
from util.printable import Printable


class Instruction(Immutable, Printable, abc.ABC):
    """
    An instruction is the smallest possible execution step that actually changes the machine state.
    Instructions are executed atomically, in the sense that intermediate states of its execution are not observable
    in the semantics.
    Instructions are very similar to the instructions that one normally finds in hardware instruction sets. However,
    we greatly reduce the number of necessary instructions by also using Terms, which in contrast to instructions
    are *functional* (i.e. terms can never change the machine state).
    """

    @staticmethod
    @abc.abstractmethod
    def print_proto(cls, out, *args):
        """
        Prints a prototype for this class of instructions to the given text stream.
        :param out: The TextIOBase object to which strings should be printed.
        :param args: The arguments that define the prototype for the instruction to be printed. Note that these arguments
                     are likely not the ones that the constructor will be called with, because prototypes exist, before
                     the program is complete and so can for example not know final jump locations yet.
        """
        pass

    @abc.abstractmethod
    def execute(self, tstate, mstate):
        """
        Executes this instruction in the given state, leading to a new state, that in particular determines which
        instruction to execute next.
        This procedure may modify the given TaskState and MachineState objects.
        :param tstate: The unsealed TaskState object that this instruction is to be executed in.
        It must be part of the given machine state.
        Any references to task-local variables will be interpreted with respect to this task state.
        :param mstate: The unsealed MachineState object that this instruction is to be executed in.
        It must contain the given task state.
        """
        pass

    @abc.abstractmethod
    def enabled(self, tstate, mstate):
        """
        Decides if executing this instruction is going to modify *any* part of the machine state, i.e. if any progress
        will be made.
        :param tstate: The task state that this instruction is to be executed in. It must be part of the given machine
        state. Any references to task-local variables will be interpreted with respect to this task state.
        :param mstate: The machine state that this instruction is to be executed in. It must contain the given task
        state.
        :return: A boolean value indicating if executing the instruction will lead to *any* change in the machine state.
        """
        pass
