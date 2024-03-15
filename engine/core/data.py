import abc
from abc import ABC

from engine.core.atomic import type_object
from engine.core.finite import FiniteValue
from engine.core.intrinsic import intrinsic_type, intrinsic_init
from engine.core.value import Value
from util import check_type
from util.immutable import Immutable


@intrinsic_type("bool", [type_object])
class VBool(FiniteValue):
    """
    Equivalent to Python's bool.
    """

    def __init__(self, value):
        """
        Wraps a bool value as a VBool value.
        :param value: The bool value to wrap.
        """
        # Finite.__new__ already took care of the value.
        super().__init__()

    def __python__(self):
        """
        Returns boolean value that this VBool represents.
        """
        return self._iindex == 1

    def print(self, out):
        out.write("True" if self._iindex == 1 else "False")

    def __repr__(self):
        return f"VBool({self._iindex == 1})"

    @property
    def type(self):
        return VBool.intrinsic_type

    def cequals(self, other):
        try:
            return self.__python__() == other.__python__()
        except AttributeError:
            return False


class VPython(Immutable, Value, ABC):
    """
    Instances of this type represent Python atomic objects as immutable Value objects.
    """

    t2i = None

    def __new__(cls, value, *args, **kwargs):
        return super().__new__(cls, value, *args, **kwargs)

    def __init__(self, value):
        # int.__new__ already took care of the value.
        super().__init__()

    @abc.abstractmethod
    def __python__(self):
        """
        Returns the Python equivalent of this value.
        """
        pass

    def print(self, out):
        out.write(super(ABC, self).__str__())

    def hash(self):
        return super(ABC, self).__hash__()

    def equals(self, other):
        return isinstance(other, type(self)) and super(ABC, self).__eq__(other)

    def bequals(self, other, bijection):
        return self.equals(other)

    def cequals(self, other):
        try:
            return self.__python__() == other.__python__()
        except AttributeError:
            return False


@intrinsic_type("int", [type_object])
class VInt(VPython, int):
    """
    Equivalent to Python's int.
    """

    @property
    def type(self):
        return VInt.intrinsic_type

    def __python__(self):
        return int(self)


@intrinsic_type("float", [type_object])
class VFloat(VPython, float):
    """
    Equivalent to Python's float.
    """

    @property
    def type(self):
        return VFloat.intrinsic_type

    def __python__(self):
        return float(self)


@intrinsic_type("str", [type_object])
class VStr(VPython, str):
    """
    Equivalent to Python's str.
    """

    @intrinsic_init()
    def __init__(self, value):
        super().__init__(value)

    @property
    def type(self):
        return VStr.intrinsic_type

    def __python__(self):
        return str(self)

    def __getitem__(self, item):
        try:
            return VStr(super(ABC, self).__getitem__(item))
        except IndexError as iex:
            raise VIndexError(str(iex))


@intrinsic_type("Exception", [type_object])
class VException(Value, Exception):
    """
    The base type for all exceptions.
    """

    def __init__(self, message, *args, pexception=None):
        """
        Creates a new exception
        :param message: The message for this exception.
        :param args: Additional constructor arguments that annotate the exception.
        :param pexception: An underlying Python exception, if it caused the exception to be created.
        """
        super().__init__(message)
        if isinstance(message, str):
            message = VStr(message)
        self._msg = check_type(message, VStr, allow_none=True)
        self._args = tuple(check_type(a, Value) for a in args)
        self._pexception = check_type(pexception, Exception, allow_none=True)

    @intrinsic_init()
    @staticmethod
    def create(cls, message):
        """
        The constructor for exceptions that is visible in Python.
        :return: An instance of the base class on which this method is called.
        """
        return cls(message)

    def print(self, out):
        out.write(type(self).__name__)
        out.write("(")
        out.write(repr(self._msg))
        out.write(", ...)")

    def __repr__(self):
        return "VException({})".format(", ".join((repr(self._msg), *map(repr, self._args))))

    @property
    def type(self):
        return type(self).intrinsic_type

    @property
    def message(self):
        """
        The message for this exception.
        """
        return self._msg

    @property
    def args(self):
        """
        Additional constructor arguments that annotate the exception.
        """
        return self._args

    @property
    def pexception(self):
        """
        The python exception that caused this exception, if any.
        """
        return self._pexception

    def _seal(self):
        self._msg.seal()
        for a in self._args:
            a.seal()

    def hash(self):
        return hash((self._msg, len(self._args)))

    def equals(self, other):
        return self is other

    def bequals(self, other, bijection):
        try:
            return bijection[id(self)] == id(other)
        except KeyError:
            bijection[id(self)] = id(other)
            if not (isinstance(other, type(self))
                    and len(self._args) == len(other._args)
                    and self._msg.bequals(other._msg, bijection)
                    and self._pexception is other._pexception):
                return False
            return all(a.bequals(b, bijection) for a, b in zip(self._args, other._args))

    def cequals(self, other):
        return self.equals(other)

    def clone_unsealed(self, clones=None):
        if clones is None:
            clones = {}
        try:
            return clones[id(self)]
        except KeyError:
            c = type(self)(self._msg, *self._args, pexception=self._pexception)
            clones[id(self)] = c
            c._args = tuple(c.clone_unsealed(clones=clones) for c in c._args)
            return c


@intrinsic_type("CancellationError")
class VCancellationError(VException):
    """
    Raised inside a task when it is cancelled.
    """

    def __init__(self, initial, msg=None):
        """
        Creates a new cancellation error.
        :param initial: Specifies if this cancellation error is to be set by TaskState.cancel, before the task had
        a chance to react to its cancellation. The first instruction to encounter an initial error will replace it
        by a non-initial one.
        """
        if msg is None:
            msg = "Cancellation!"
        super().__init__(msg)
        self._initial = check_type(initial, bool)

    @property
    def initial(self):
        """
        Indicates if this is the initial error that was set by TaskState.cancel before the task had a chance to
        handle the error.
        """
        return self._initial

    def hash(self):
        return hash(self._initial) ^ hash(self.message)

    def bequals(self, other, bijection):
        return super().bequals(other, bijection) and self._initial == other._initial

    def clone_unsealed(self, clones=None):
        if clones is None:
            clones = {}
        try:
            return clones[id(self)]
        except KeyError:
            c = VCancellationError(self._initial, msg=self.message)
            clones[id(self)] = c
            return c


@intrinsic_type("RuntimeError")
class VRuntimeError(VException):
    """
    Raised when an error occurs at VM runtime, for logical reasons that cannot be described by another
    exception type.
    """
    pass


@intrinsic_type("IndexError")
class VIndexError(VException):
    """
    Spek equivalent of Python's IndexError.
    """
    pass


@intrinsic_type("KeyError")
class VKeyError(VException):
    """
    Raised when a mapping is missing a requested key.
    """
    pass
