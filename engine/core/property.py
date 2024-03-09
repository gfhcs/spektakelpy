import abc
from abc import ABC

from engine.core.type import Type
from engine.core.value import Value


class Property(Value, ABC):
    """
    Represents an instance property.
    """

    machine_type = Type("property", [Type.get_instance_object()], [], {})

    @property
    def type(self):
        return Property.__type

    @property
    @abc.abstractmethod
    def getter_procedure(self):
        """
        The getter procedure for this property.
        """
        pass

    @property
    @abc.abstractmethod
    def setter_procedure(self):
        """
        Either None (in case of a readonly property), or the setter procedure for this property.
        """
        pass



