import abc
from abc import ABC

from engine.core.type import Type
from engine.core.value import Value


class Procedure(Value, ABC):
    """
    Represents an executable procedure.
    """
    machine_type = Type("procedure", [Type.get_instance_object()], [], {})

    @property
    def type(self):
        return Procedure.machine_type

    @abc.abstractmethod
    def initiate(self, tstate, mstate, *args):
        """
        Modifies the given machine state and task states in order to initiate execution of this procedure.
        :param tstate: The unsealed TaskState object that this instruction is to be executed in.
        It must be part of the given machine state.
        :param mstate: The unsealed MachineState object that this instruction is to be executed in.
        It must contain the given task state.
        :param args: The argument Values that this intrinsic procedure is being called for.
        :return: If the initiation of the call to this procedure immediately leads to the conclusion of the call,
                 a Value object representing the return value is returned. Otherwise, None is returned.
        :raises: Exceptions derived from Value, if errors occur during initiation.
        """
        pass
