import abc
from util.immutable import Sealable


class Value(Sealable, abc.ABC):
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

# TODO: Every object has an identity, a type and a value. An object’s identity never changes once it has been created; you may think of it as the object’s address in memory.

# TODO: We need these runtime objects: bool, int, float, str, tuple, list, dict, object, type, exception, task, function, module

class Procedure(abc.ABC):
    pass

class Struct(Value):
    pass

class DException(Value):

    def __init__(self, message):
        super().__init__()
        self._msg = message

    def hash(self):
        return hash(self._msg)

    def equals(self, other):
        pass

    def clone_unsealed(self):
        pass


class MachineError(DException):
    """
    An error that occurs as the semantic result of executing a machine program.
    """

    def __init__(self, msg):
        super().__init__()
        self._msg = msg


class EvaluationException(Exception):
    # TODO: This must be a value!
    pass