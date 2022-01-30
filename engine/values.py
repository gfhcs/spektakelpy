import abc
from util.immutable import ImmutableEquatable


class Value(abc.ABC, ImmutableEquatable):
    """
    Represents a runtime value.
    """

    @property
    @abc.abstractmethod
    def type(self):
        """
        The type that this value belongs to.
        :return: A Type object.
        """
        pass
