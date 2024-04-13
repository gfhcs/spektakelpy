import abc
from abc import ABC

from engine.core.atomic import type_object
from engine.core.finite import FiniteValue
from engine.core.intrinsic import intrinsic_type, intrinsic_init, intrinsic_member
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
        out.write(str(self.__python__()))

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

    def chash(self):
        return self.hash()


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


class VIterator(Value, ABC):
    """
    Represents the state of an iteration over an iterable.
    The subclasses of this class must fulfill the following requirements:
        1. It must either be an IntrinsicType, or override Value.type.
        2. It must either override Value._seal Value.clone_unsealed and Value.bequals, or cannot contain any subvalues.
    """

    def __init__(self, iterable):
        """
        Creates a new VIterator.
        :param iterable: The iterable object this VIterator belongs to.
        """
        super().__init__()
        self._iterable = iterable

    @property
    def iterable(self):
        """
        The iterable that this VIterator belongs to.
        """
        return self._iterable

    @property
    def type(self):
        return type(self).intrinsic_type

    def equals(self, other):
        return self is other

    def _seal(self):
        self._iterable.seal()

    def bequals(self, other, bijection):
        try:
            return bijection[id(self)] == id(other)
        except KeyError:
            bijection[id(self)] = id(other)
            return (isinstance(other, type(self))
                    and self.iterable.bequals(other.iterable, bijection)
                    and self.sequals(other))

    def cequals(self, other):
        return self is other

    def chash(self):
        return self.iterable.chash()

    def hash(self):
        return self.iterable.hash()

    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    @abc.abstractmethod
    def next(self):
        """
        Like Python's __next__, this procedure returns the next element of an iteration.
        :exception VStopIteration: If there is no next iteration element.
        :return: A Value object.
        """
        pass

    @abc.abstractmethod
    def sequals(self, other):
        """
        Decides if this iterator represents exactly the same iteration state as another iterator.
        :param other: A VIterator object that is of the same type as self and belongs to the same iterable.
        :return: A bool value.
        """
        pass

    @abc.abstractmethod
    def copy_unsealed(self):
        """
        Returns an unsealed copy of this iterator. This method is called by self.clone_unsealed in order to replicate
        the state of this iterator.
        :return: A VIterator i with i.sequals(self).
        """
        pass

    def clone_unsealed(self, clones=None):
        if clones is None:
            clones = {}
        try:
            return clones[id(self)]
        except KeyError:
            c = self.copy_unsealed()
            clones[id(self)] = c
            c._iterable = self._iterable.clone_unsealed(clones=clones)
            return c


@intrinsic_type("indexing_iterator", [type_object])
class VIndexingIterator(VIterator):
    """
    An iterator the state of which is encoded by an index that is incremented after every iteration.
    This iterator works will all immutable, indexable sequence types.
    """

    def __init__(self, s):
        super().__init__(check_type(s, Value))
        self._i = 0

    def sequals(self, other):
        return self._i == other._i

    def copy_unsealed(self):
        c = VIndexingIterator(self.iterable)
        c._i = self._i
        return c

    def print(self, out):
        out.write("indexing_iterator(")
        self.iterable.print(out)
        out.write(f", {self._i})")

    @intrinsic_member("__next__")
    def next(self):
        try:
            c = self.iterable[VInt(self._i)]
            self._i += 1
            return c
        except VIndexError:
            raise VStopIteration("End of iterator!")


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
        return str.__str__(self)

    def __getitem__(self, item):
        try:
            return VStr(super(ABC, self).__getitem__(item))
        except IndexError as iex:
            raise VIndexError(str(iex))

    def __iter__(self):
        return VIndexingIterator(self)


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

    def chash(self):
        return self.type.chash()

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


@intrinsic_type("StopIteration")
class VStopIteration(VException, StopIteration):
    """
    Raised when an iteration runs out of elements to iterate over.
    """
    pass
