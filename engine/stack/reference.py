import abc

from engine.core.intrinsic import intrinsic
from engine.core.type import Type
from engine.core.value import Value


@intrinsic("reference", [Type.get_instance_object()])
class Reference(Value, abc.ABC):
    """
    A reference is a part of a machine state that can point to another part of a machine state.
    """

    def type(self):
        return Reference.machine_type

    @abc.abstractmethod
    def write(self, tstate, mstate, value):
        """
        Updates the value stored at the location that this reference is pointing to.
        :param tstate: The TaskState in the context of which this reference is to be interpreted. It must be part
                       of the given mstate.
        :param mstate: The MachineState in the context of which this reference is to be interpreted. It must contain
                       tstate.
        :param value: The value to store at the location that this reference is pointing to.
        """
        pass

    @abc.abstractmethod
    def read(self, tstate, mstate):
        """
        Obtains the value that this reference is pointing to.
        :param tstate: The TaskState in the context of which this reference is to be interpreted. It must be part
                       of the given mstate.
        :param mstate: The MachineState in the context of which this reference is to be interpreted. It must contain
                       tstate.
        :return: The object pointed to by this reference.
        """
        pass
