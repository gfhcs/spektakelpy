import abc
from abc import ABC

from engine.core.atomic import type_object
from engine.core.finite import FiniteValue
from engine.core.intrinsic import intrinsic_type
from engine.core.value import Value
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
        return "VBool(True)" if self._iindex == 1 else "VBool(False)"

    @property
    def type(self):
        return VBool.intrinsic_type

    def cequals(self, other):
        return self.__python__() == other.__python__()


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
        out.write(self)

    def hash(self):
        return super(ABC, self).__hash__()

    def equals(self, other):
        return isinstance(other, type(self)) and super(ABC, self).__eq__(other)

    def bequals(self, other, bijection):
        return self.equals(other)

    def cequals(self, other):
        return self.__python__() == other.__python__()


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

    @property
    def type(self):
        return VStr.intrinsic_type

    def __python__(self):
        return str(self)
