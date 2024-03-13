from engine.core.atomic import type_object
from engine.core.intrinsic import intrinsic_type
from engine.core.value import Value
from util import check_type
from util.finite import Finite
from util.immutable import Immutable


@intrinsic_type("bool", [type_object])
class VBool(Finite, Value):
    """
    Equivalent to Python's bool.
    """

    def __init__(self, value):
        super().__init__(int(value.value if isinstance(value, VBool) else check_type(value, bool)))

    @property
    def value(self):
        """
        The boolean value that this VBool represents.
        :return: A bool.
        """
        return self._iindex == 1

    def print(self, out):
        out.write("True" if self.value else "False")

    def __repr__(self):
        return "VBool(True)" if self.value else "VBool(False)"

    @property
    def type(self):
        return VBool.intrinsic_type

    def bequals(self, other, bijection):
        return self.equals(other)

    def cequals(self, other):
        return isinstance(other, (VBool, VInt, VFloat)) and self.value == other.value

    def __lt__(self, other):
        return VBool(self.value < other.value)

    def __le__(self, other):
        return VBool(self.value <= other.value)

    def __gt__(self, other):
        return VBool(self.value > other.value)

    def __ge__(self, other):
        return VBool(self.value >= other.value)

    def __bool__(self):
        return self.value

    def __int__(self):
        return int(self.value)

    def __float__(self):
        return float(self.value)

    def __neg__(self):
        return VInt(-self.value)

    def __pos__(self):
        return VInt(+self.value)

    def __abs__(self):
        return VInt(abs(self.value))

    def __invert__(self):
        return VInt(~self.value)

    def __and__(self, other):
        return VBool(self.value & other.value)

    def __xor__(self, other):
        return VBool(self.value ^ other.value)

    def __or__(self, other):
        return VBool(self.value | other.value)

    def __lshift__(self, other):
        return VInt(self.value << int(other))

    def __rshift__(self, other):
        return VInt(self.value >> int(other))

    def __add__(self, other):
        return VInt(self.value + other.value)

    def __sub__(self, other):
        return VInt(self.value - other.value)

    def __mul__(self, other):
        return VInt(self.value * other.value)

    def __truediv__(self, other):
        return VFloat(self.value / other.value)

    def __floordiv__(self, other):
        return VInt(self.value // other.value)

    def __mod__(self, other):
        return VInt(self.value % other.value)

    def __pow__(self, other):
        return VInt(self.value ** other.value)


def p2s(x):
    """
    Casts the numeric Python value to the corresponding Spek value.
    :param x: A numeric Python value.
    :return: A corresponding Spek value of appropriate type.
    """
    if isinstance(x, int):
        return VInt(x)
    elif isinstance(x, float):
        return VFloat(x)
    else:
        raise TypeError(f"p2s cannot convert values of Python type {type(x)}!")


@intrinsic_type("int", [type_object])
class VInt(Immutable, Value):
    """
    Equivalent to Python's int.
    """

    def __init__(self, value=0):
        super().__init__()
        self._value = check_type(value, int)

    def print(self, out):
        out.write(str(self._value))

    def __repr__(self):
        return "VInt({})".format(self._value)

    @property
    def type(self):
        return VInt.intrinsic_type

    def hash(self):
        return self._value

    def equals(self, other):
        return isinstance(other, VInt) and self._value == other._value

    def bequals(self, other, bijection):
        return self.equals(other)

    def cequals(self, other):
        return isinstance(other, (VBool, VInt, VFloat)) and self._value == other._value

    def __lt__(self, other):
        return VBool(self._value < other._value)

    def __le__(self, other):
        return VBool(self._value <= other._value)

    def __gt__(self, other):
        return VBool(self._value > other._value)

    def __ge__(self, other):
        return VBool(self._value >= other._value)

    def __bool__(self, other):
        return bool(self._value)

    def __int__(self):
        return self._value

    def __float__(self):
        return float(self._value)

    def __neg__(self):
        return VInt(-self._value)

    def __pos__(self):
        return VInt(+self._value)

    def __abs__(self):
        return VInt(abs(self._value))

    def __invert__(self):
        return VInt(~self._value)

    def __and__(self, other):
        return VInt(self._value & other._value)

    def __xor__(self, other):
        return VInt(self._value ^ other._value)

    def __or__(self, other):
        return VInt(self._value | other._value)

    def __lshift__(self, other):
        return VInt(self._value << int(other))

    def __rshift__(self, other):
        return VInt(self._value >> int(other))

    def __add__(self, other):
        return p2s(self._value + other._value)

    def __sub__(self, other):
        return p2s(self._value - other._value)

    def __mul__(self, other):
        return p2s(self._value * other._value)

    def __truediv__(self, other):
        return VFloat(self._value / other._value)

    def __floordiv__(self, other):
        return VInt(self._value // other._value)

    def __mod__(self, other):
        return VInt(self._value % other._value)

    def __pow__(self, other):
        return VInt(self._value ** other._value)


@intrinsic_type("float", [type_object])
class VFloat(Immutable, Value):
    """
    Equivalent to Python's float.
    """

    def __init__(self, value=0.0):
        super().__init__()
        self._value = check_type(value, float)

    def print(self, out):
        out.write(str(self._value))

    def __repr__(self):
        return "VFloat({})".format(self._value)

    @property
    def type(self):
        return VFloat.intrinsic_type

    def hash(self):
        return hash(self._value)

    def equals(self, other):
        return isinstance(other, VFloat) and self._value == other._value

    def bequals(self, other, bijection):
        return self.equals(other)

    def cequals(self, other):
        return isinstance(other, (VBool, VInt, VFloat)) and self._value == other._value

    def __lt__(self, other):
        return VBool(self._value < other._value)

    def __le__(self, other):
        return VBool(self._value <= other._value)

    def __gt__(self, other):
        return VBool(self._value > other._value)

    def __ge__(self, other):
        return VBool(self._value >= other._value)

    def __bool__(self, other):
        return bool(self._value)

    def __int__(self):
        return int(self._value)

    def __float__(self):
        return self._value

    def __neg__(self):
        return VFloat(-self._value)

    def __pos__(self):
        return VFloat(+self._value)

    def __abs__(self):
        return VFloat(abs(self._value))

    def __invert__(self):
        return VFloat(~self._value)

    def __add__(self, other):
        return VFloat(self._value + other._value)

    def __sub__(self, other):
        return VFloat(self._value - other._value)

    def __mul__(self, other):
        return VFloat(self._value * other._value)

    def __truediv__(self, other):
        return VFloat(self._value / other._value)

    def __floordiv__(self, other):
        return VFloat(self._value // other._value)

    def __mod__(self, other):
        return VFloat(self._value % other._value)

    def __pow__(self, other):
        return VFloat(self._value ** other._value)


@intrinsic_type("str", [type_object])
class VStr(Immutable, Value):
    """
    Equivalent to Python's str.
    """

    def __init__(self, value=""):
        super().__init__()
        self._value = check_type(value, str)

    def print(self, out):
        out.write(repr(self._value))

    @property
    def string(self):
        return self._value

    def __repr__(self):
        return "VString(\"{}\")".format(self._value)

    @property
    def type(self):
        return VStr.intrinsic_type

    def hash(self):
        return hash(self._value)

    def equals(self, other):
        return self is other

    def bequals(self, other, bijection):
        try:
            return bijection[id(self)] == id(other)
        except KeyError:
            bijection[id(self)] = id(other)
            return isinstance(other, VStr) and self._value == other._value

    def cequals(self, other):
        return isinstance(other, VStr) and self._value == other._value

    def __contains__(self, item):
        return item.string in self._value

    def __lt__(self, other):
        return VBool(self._value < other._value)

    def __le__(self, other):
        return VBool(self._value <= other._value)

    def __gt__(self, other):
        return VBool(self._value > other._value)

    def __ge__(self, other):
        return VBool(self._value >= other._value)
