import abc

from util import check_type
from util.immutable import Sealable
from .types import TBuiltin


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
    """
    Equivalent of Python's 'None'.
    """

    @property
    def type(self):
        return TBuiltin.none

    def hash(self):
        return 0

    def equals(self, other):
        return isinstance(other, VNone)

    def _seal(self):
        pass

    def clone_unsealed(self, cloned=None):
        return self

    def __str__(self):
        return "None"

    def __repr__(self):
        return "VNone.instance"


VNone.instance = VNone()


class VBoolean(Value):
    """
    Equivalent to Python's bool.
    """

    def __init__(self, value):
        super().__init__()
        self._value = check_type(value, bool)

    @staticmethod
    def from_bool(b):
        """
        Converts a bool to a VBoolean object, in a way that saves memory.
        :param b: The bool to convert.
        :return: A VBoolean object.
        """
        return VBoolean.true if b else VBoolean.false

    def __str__(self):
        return "True" if self._value else "False"

    def __repr__(self):
        return "VBool.true" if self._value else "VBool.false"

    @property
    def type(self):
        return TBuiltin.bool

    def hash(self):
        return hash(self._value)

    def equals(self, other):
        return isinstance(other, VBoolean) and self._value == other._value

    def _seal(self):
        pass

    def clone_unsealed(self, cloned=None):
        return self

    def __lt__(self, other):
        return VBoolean.from_bool(self._value < other._value)

    def __le__(self, other):
        return VBoolean.from_bool(self._value <= other._value)

    def __gt__(self, other):
        return VBoolean.from_bool(self._value > other._value)

    def __ge__(self, other):
        return VBoolean.from_bool(self._value >= other._value)

    def __bool__(self, other):
        return self._value

    def __int__(self):
        return int(self._value)

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
        return VBoolean.from_bool(self._value & other._value)

    def __xor__(self, other):
        return VBoolean.from_bool(self._value ^ other._value)

    def __or__(self, other):
        return VBoolean.from_bool(self._value | other._value)

    def __lshift__(self, other):
        return VInt(self._value << int(other))

    def __rshift__(self, other):
        return VInt(self._value >> int(other))

    def __add__(self, other):
        return VInt(self._value + other._value)

    def __sub__(self, other):
        return VInt(self._value - other._value)

    def __mul__(self, other):
        return VInt(self._value * other._value)

    def __truediv__(self, other):
        return VFloat(self._value / other._value)

    def __floordiv__(self, other):
        return VInt(self._value // other._value)

    def __mod__(self, other):
        return VInt(self._value % other._value)

    def __pow__(self, other):
        return VInt(self._value ** other._value)


VBoolean.true = VBoolean(True)
VBoolean.false = VBoolean(False)


class VInt(Value):
    """
    Equivalent to Python's int.
    """

    def __init__(self, value):
        super().__init__()
        self._value = check_type(value, int)

    def __str__(self):
        return str(self._value)

    def __repr__(self):
        return "VInt({})".format(self._value)

    @property
    def type(self):
        return TBuiltin.int

    def hash(self):
        return hash(self._value)

    def equals(self, other):
        return isinstance(other, VInt) and self._value == other._value

    def _seal(self):
        pass

    def clone_unsealed(self, cloned=None):
        return self

    def __lt__(self, other):
        return VBoolean.from_bool(self._value < other._value)

    def __le__(self, other):
        return VBoolean.from_bool(self._value <= other._value)

    def __gt__(self, other):
        return VBoolean.from_bool(self._value > other._value)

    def __ge__(self, other):
        return VBoolean.from_bool(self._value >= other._value)

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
        return VInt(self._value + other._value)

    def __sub__(self, other):
        return VInt(self._value - other._value)

    def __mul__(self, other):
        return VInt(self._value * other._value)

    def __truediv__(self, other):
        return VFloat(self._value / other._value)

    def __floordiv__(self, other):
        return VInt(self._value // other._value)

    def __mod__(self, other):
        return VInt(self._value % other._value)

    def __pow__(self, other):
        return VInt(self._value ** other._value)


class VFloat(Value):
    """
    Equivalent to Python's float.
    """

    def __init__(self, value):
        super().__init__()
        self._value = check_type(value, float)

    def __str__(self):
        return str(self._value)

    def __repr__(self):
        return "VFloat({})".format(self._value)

    @property
    def type(self):
        return TBuiltin.float

    def hash(self):
        return hash(self._value)

    def equals(self, other):
        return isinstance(other, VFloat) and self._value == other._value

    def _seal(self):
        pass

    def clone_unsealed(self, cloned=None):
        return self

    def __lt__(self, other):
        return VBoolean.from_bool(self._value < other._value)

    def __le__(self, other):
        return VBoolean.from_bool(self._value <= other._value)

    def __gt__(self, other):
        return VBoolean.from_bool(self._value > other._value)

    def __ge__(self, other):
        return VBoolean.from_bool(self._value >= other._value)

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


class VString(Value):
    """
    Equivalent to Python's str.
    """

    def __init__(self, value):
        super().__init__()
        self._value = check_type(value, str)

    def __str__(self):
        return str(self._value)

    def __repr__(self):
        return "VString(\"{}\")".format(self._value)

    @property
    def type(self):
        return TBuiltin.str

    def hash(self):
        return hash(self._value)

    def equals(self, other):
        return isinstance(other, VString) and self._value == other._value

    def _seal(self):
        pass

    def clone_unsealed(self, cloned=None):
        return self

    def __lt__(self, other):
        return VBoolean.from_bool(self._value < other._value)

    def __le__(self, other):
        return VBoolean.from_bool(self._value <= other._value)

    def __gt__(self, other):
        return VBoolean.from_bool(self._value > other._value)

    def __ge__(self, other):
        return VBoolean.from_bool(self._value >= other._value)


class VTuple(Value):
    """
    Equivalent to Python's tuples.
    """

    def __init__(self, *components):
        super().__init__()
        self._comps = tuple(check_type(c, Value) for c in components)

    def __str__(self):
        return "({})".format(", ".join(self._comps))

    def __repr__(self):
        return "VTuple({})".format(", ".join(self._comps))

    @property
    def type(self):
        return TBuiltin.tuple

    def hash(self):
        return hash(self._comps)

    def equals(self, other):
        return isinstance(other, VTuple) and self._comps == other._comps

    def _seal(self):
        for c in self._comps:
            c.seal()

    def clone_unsealed(self, clones=None):
        if clones is None:
            clones = {}
        try:
            return clones[id(self)]
        except KeyError:
            c = VTuple(*(c.clone_unsealed(clones=clones) for c in self._comps))
            clones[id(self)] = c
            return c

    def __len__(self):
        return len(self._comps)

    def __iter__(self):
        return iter(self._comps)

    def __getitem__(self, item):
        return self._comps[item]

    def __lt__(self, other):
        return VBoolean.from_bool(self._comps < other._comps)

    def __le__(self, other):
        return VBoolean.from_bool(self._comps <= other._comps)

    def __gt__(self, other):
        return VBoolean.from_bool(self._comps > other._comps)

    def __ge__(self, other):
        return VBoolean.from_bool(self._comps >= other._comps)


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
