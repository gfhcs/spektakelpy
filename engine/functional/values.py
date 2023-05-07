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

class VNone(Value):
    # TODO: Must provide 1 instance object.
    pass


class VBoolean(Value):
    # TODO: Must implement boolean operators in Python!
    pass


class VInt(Value):
    # TODO: Must implement numeric operators in Python!
    pass


class VFloat(Value):
    # TODO: Must implement numeric operators in Python!
    pass


class VString(Value):
    pass


class VTuple(Value):
    # TODO: Implement tuples.
    pass

class VList(Value):
    # TODO: Implement lists.
    pass

class VDict(Value):
    # TODO: Implement dicts.
    pass


class VException(Value):

    def __init__(self, message):
        super().__init__()
        self._msg = message

    def hash(self):
        return hash(self._msg)

    def equals(self, other):
        pass

    def clone_unsealed(self, clones=None):
        pass


class EvaluationException(VException):
    pass


class VTypeError(VException):
    pass


class VJumpException(VException):
    pass


class VReturnException(VJumpException):
    pass


class VBreakException(VJumpException):
    pass


class VContinueException(VJumpException):
    pass


class VAttributeError(VException):
    pass


class VNamespace(Value):
    """
    A mapping from names to objects.
    """

    def __init__(self, **kwargs):
        """
        Creates a new namespace.
        :param kwargs: A mapping form strings to Value objects that this namespace is to be initialized with.
        """
        pass

    def adjoin(self, name, value):
        """
        Manipulates this namespace to map the given name to the given value.
        :param name: A string.
        :param value: A runtime object that the name is to be mapped to.
        """
        pass

    def lookup(self, name):
        """
        Looks up the given name in this name space.
        :param name: The name to look up.
        :return: The runtime object that was retrieved.

        """
        pass


class VProcedure(abc.ABC):
    pass


class VProperty(Value):
    pass


class VModule(Value):
    pass
