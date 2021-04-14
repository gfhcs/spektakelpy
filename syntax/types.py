import abc
from core import compact
from util import check_type


class Value(compact.CompactObject):
    """
    A value that occurs at runtime of a syntactic process.
    """

    @classmethod
    def name(cls):
        """
        The name by which this type can be referred to syntactically.
        :return: A string.
        """
        return "Value"

    @classmethod
    @abc.abstractmethod
    def default(cls):
        """
        Returns the default value of this type.
        :return: A Value object for which self.hastype gives True.
        """
        pass


class PythonicValue(Value):
    """
    A type that simulates a Python type.
    """
    def __init__(self, p):
        """
        Creates a new Pythonic value.
        :param p: The Python object to represent.
        """
        super().__init__()
        self._p = p

    @classmethod
    def name(cls):
        return "PythonicValue"

    def equal(self, other):
        return isinstance(other, type(self)) and self._p == other._p

    def hash(self):
        return hash(self._p)

    @property
    def value(self):
        """
        The Python value represented by this instance.
        """
        return self._p


class Bool(PythonicValue):
    """
    Represents boolean values.
    """

    def __init__(self, b):
        check_type(b, bool)
        super().__init__(b)

    @classmethod
    def name(cls):
        return "bool"

    @classmethod
    def default(cls):
        return Bool(False)


class NumericValue(PythonicValue):
    """
    Represents numeric values.
    """

    @classmethod
    def name(cls):
        return "NumericValue"

    @classmethod
    def default(cls):
        return cls(0)


class Int(NumericValue):
    """
    Represents integer values.
    """
    def __init__(self, i):
        check_type(i, int)
        super().__init__(i)

    @classmethod
    def name(cls):
        return "int"


class Float(NumericValue):
    """
    Represents floating point values.
    """

    def __init__(self, f):
        check_type(f, float)
        super().__init__(f)

    @classmethod
    def name(cls):
        return "float"


class String(PythonicValue):
    """
    Represents Python strings.
    """

    def __init__(self, s):
        check_type(s, str)
        super().__init__(s)

    @classmethod
    def name(cls):
        return "string"

    @classmethod
    def default(cls):
        return String("")


class TupleValue(Value):
    """
    Values of this type are tuples with a specific signature of component types.
    """

    def __init__(self, *components):
        super().__init__()
        for c, t in zip(components, type(self).ctypes()):
            check_type(c, t)
        self._cs = components

    @classmethod
    def name(cls):
        return " * ".join((t.name for t in cls.ctypes()))

    @classmethod
    @abc.abstractmethod
    def ctypes(cls):
        """
        The tuple of component types for the tuple type.
        """
        pass

    @classmethod
    def default(cls):
        return TupleValue(*(ct.default for ct in cls.ctypes()))

    def equal(self, other):
        return isinstance(other, TupleValue) and self._cs == other._cs

    def hash(self):
        return hash(self._cs)


__tupletypes = {}


def TupleType(*ctypes):
    """
    Constructs a tuple type with the given component types.
    :param ctypes: The component types for the tuple type to construct.
    :return: A subclass of TupleValue.
    """

    key = tuple(id(t) for t in ctypes)

    try:
        return __tupletypes[key]
    except KeyError:
        class T(TupleValue):
            @classmethod
            def ctypes(cls):
                return ctypes

        __tupletypes[key] = T
        return T


class StructValue(Value):
    """
    Values of this type are basically mappings from member names to components.
    """

    def __init__(self, **membervalues):
        super().__init__()

        if len(membervalues) != len(self.mtypes()):
            raise ValueError("This struct type has {e} members, but {f} member values were given!"
                             .format(e=len(self.mtypes()), f = len(membervalues)))

        self._m = {}
        for k, t in self.mtypes():
            self._m[k] = check_type(membervalues[k], t)

    @classmethod
    def name(cls):
        return "{" + ", ".join((k + ": " + t.name for k, t in cls.mtypes().items())) + "}"

    @classmethod
    @abc.abstractmethod
    def mtypes(cls):
        """
        A dict mapping member names to member types.
        """
        pass

    @classmethod
    def default(cls):
        return StructValue(**{k: t.default() for k, t in cls.mtypes()})

    def equal(self, other):
        return type(self) is type(other) and all(self._m[k] == other._m[k] for k in self.mtypes().keys())

    def hash(self):
        h = 0
        for val in self._m.values():
            h ^= hash(val)
        return h


__structtypes = {}

def StructType(**mtypes):
    """
    Constructs a struct type with the given member types.
    :param mtypes: The member types for the struct type to construct.
    :return: A subclass of StructValue.
    """

    key = tuple((k, id(t)) for k, t in mtypes.items())

    try:
        return __structtypes[key]
    except KeyError:
        class T(StructValue):
            @classmethod
            def mtypes(cls):
                return mtypes

        __structtypes[key] = T
        return T