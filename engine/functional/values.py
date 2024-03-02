from enum import Enum

from engine.intrinsic import IntrinsicInstanceMethod
from util import check_type, check_types
from util.immutable import check_unsealed
from . import Value


class VNone(Value):
    """
    Equivalent of Python's 'None'.
    """

    @property
    def type(self):
        return TBuiltin.none

    def hash(self):
        return 0

    def bequals(self, other, bijection):
        return isinstance(other, VNone)

    def _seal(self):
        pass

    def clone_unsealed(self, clones=None):
        return self

    def print(self, out):
        out.write("None")

    def __repr__(self):
        return "VNone.instance"


VNone.instance = VNone()


class VBool(Value):
    """
    Equivalent to Python's bool.
    """

    def __init__(self, value=False):
        super().__init__()
        self._value = check_type(value, bool)

    @staticmethod
    def from_bool(b):
        """
        Converts a bool to a VBoolean object, in a way that saves memory.
        :param b: The bool to convert.
        :return: A VBoolean object.
        """
        return VBool.true if b else VBool.false

    def print(self, out):
        out.write("True" if self._value else "False")

    def __repr__(self):
        return "VBool.true" if self._value else "VBool.false"

    @property
    def type(self):
        return TBuiltin.bool

    def hash(self):
        return hash(self._value)

    def bequals(self, other, bijection):
        return isinstance(other, (VBool, VInt, VFloat)) and self._value == other._value

    def _seal(self):
        pass

    def clone_unsealed(self, clones=None):
        return self

    def __lt__(self, other):
        return VBool.from_bool(self._value < other._value)

    def __le__(self, other):
        return VBool.from_bool(self._value <= other._value)

    def __gt__(self, other):
        return VBool.from_bool(self._value > other._value)

    def __ge__(self, other):
        return VBool.from_bool(self._value >= other._value)

    def __bool__(self):
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
        return VBool.from_bool(self._value & other._value)

    def __xor__(self, other):
        return VBool.from_bool(self._value ^ other._value)

    def __or__(self, other):
        return VBool.from_bool(self._value | other._value)

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


VBool.true = VBool(True)
VBool.false = VBool(False)


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
        raise TypeError(f"p2s cannot convert values of Pyton type {type(x)}!")


class VInt(Value):
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
        return TBuiltin.int

    def hash(self):
        return self._value

    def bequals(self, other, bijection):
        return isinstance(other, (VBool, VInt, VFloat)) and self._value == other._value

    def _seal(self):
        pass

    def clone_unsealed(self, clones=None):
        return self

    def __lt__(self, other):
        return VBool.from_bool(self._value < other._value)

    def __le__(self, other):
        return VBool.from_bool(self._value <= other._value)

    def __gt__(self, other):
        return VBool.from_bool(self._value > other._value)

    def __ge__(self, other):
        return VBool.from_bool(self._value >= other._value)

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


class VFloat(Value):
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
        return TBuiltin.float

    def hash(self):
        return hash(self._value)

    def bequals(self, other, bijection):
        return isinstance(other, (VBool, VInt, VFloat)) and self._value == other._value

    def _seal(self):
        pass

    def clone_unsealed(self, clones=None):
        return self

    def __lt__(self, other):
        return VBool.from_bool(self._value < other._value)

    def __le__(self, other):
        return VBool.from_bool(self._value <= other._value)

    def __gt__(self, other):
        return VBool.from_bool(self._value > other._value)

    def __ge__(self, other):
        return VBool.from_bool(self._value >= other._value)

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


class VStr(Value):
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
        return TBuiltin.str

    def hash(self):
        return hash(self._value)

    def bequals(self, other, bijection):
        try:
            return bijection[id(self)] == id(other)
        except KeyError:
            bijection[id(self)] = id(other)
            return isinstance(other, VStr) and self._value == other._value

    def _seal(self):
        pass

    def clone_unsealed(self, clones=None):
        return self

    def __contains__(self, item):
        return item.string in self._value

    def __lt__(self, other):
        return VBool.from_bool(self._value < other._value)

    def __le__(self, other):
        return VBool.from_bool(self._value <= other._value)

    def __gt__(self, other):
        return VBool.from_bool(self._value > other._value)

    def __ge__(self, other):
        return VBool.from_bool(self._value >= other._value)


class VCell(Value):
    """
    An object that references another object.
    """

    def __init__(self, ref):
        """
        Creates a new cell.
        :param ref: The object this cell should contain.
        """
        super().__init__()
        self._ref = check_type(ref, Value)

    @property
    def value(self):
        """
        The object contained in this cell.
        :return: A Value.
        """
        return self._ref

    @value.setter
    def value(self, value):
        check_unsealed(self)
        self._ref = check_type(value, Value)

    def print(self, out):
        out.write("Cell(")
        self._ref.print(out)
        out.write(")")

    def __repr__(self):
        return f"VCell({repr(self._ref)})"

    @property
    def type(self):
        return TBuiltin.cell

    def hash(self):
        return hash(self._ref) ^ 47

    def bequals(self, other, bijection):
        try:
            return bijection[id(self)] == id(other)
        except KeyError:
            bijection[id(self)] = id(other)
            return isinstance(other, VCell) and self._ref.bequals(other._ref, bijection)

    def _seal(self):
        self._ref.seal()

    def clone_unsealed(self, clones=None):
        if clones is None:
            clones = {}
        try:
            return clones[id(self)]
        except KeyError:
            c = VCell(self._ref)
            clones[id(self)] = c
            c._ref = self._ref.clone_unsealed(clones=clones)
            return c


class VTuple(Value):
    """
    Equivalent to Python's tuples.
    """

    def __init__(self, *components):
        super().__init__()
        self._comps = tuple(check_type(c, Value) for c in components)

    def print(self, out):
        out.write("(")
        prefix = ""
        for c in self._comps:
            out.write(prefix)
            c.print(out)
            prefix = ", "
        out.write(")")

    def __repr__(self):
        return "VTuple({})".format(", ".join(self._comps))

    @property
    def type(self):
        return TBuiltin.tuple

    def hash(self):
        return len(self._comps)

    def bequals(self, other, bijection):
        # Python can actually tell tuples apart by their identity!
        try:
            return bijection[id(self)] == id(other)
        except KeyError:
            bijection[id(self)] = id(other)
            if not (isinstance(other, VTuple)
                    and len(self._comps) == len(other._comps)):
                return False
            return all(a.bequals(b, bijection) for a, b in zip(self._comps, other._comps))

    def _seal(self):
        for c in self._comps:
            c.seal()

    def clone_unsealed(self, clones=None):
        if clones is None:
            clones = {}
        try:
            return clones[id(self)]
        except KeyError:
            c = VTuple(*self._comps)
            clones[id(self)] = c
            c._comps = tuple(c.clone_unsealed(clones=clones) for c in self._comps)
            return c

    def __len__(self):
        return len(self._comps)

    def __iter__(self):
        return iter(self._comps)

    def __getitem__(self, key):
        return self._comps[int(check_type(key, Value))]

    def __lt__(self, other):
        return VBool.from_bool(self._comps < other._comps)

    def __le__(self, other):
        return VBool.from_bool(self._comps <= other._comps)

    def __gt__(self, other):
        return VBool.from_bool(self._comps > other._comps)

    def __ge__(self, other):
        return VBool.from_bool(self._comps >= other._comps)


class VList(Value):
    """
    Equivalent to Python's lists.
    """

    def __init__(self, items=None):
        super().__init__()
        self._items = [] if items is None else [check_type(x, Value) for x in items]

    @IntrinsicInstanceMethod
    def append(self, item):
        """
        Appends an item to this list.
        :param item: The item to append.
        """
        if self.sealed:
            raise RuntimeError("This VList instance has been sealed and can thus not be modified anymore!")
        return self._items.append(check_type(item, Value))

    @IntrinsicInstanceMethod
    def pop(self, index):
        """
        Pops an item from this list.
        :param index: The index of the item to pop.
        :return: The popped item.
        """
        if self.sealed:
            raise RuntimeError("This VList instance has been sealed and can thus not be modified anymore!")
        return self._items.pop(int(index))

    @IntrinsicInstanceMethod
    def insert(self, index, item):
        """
        Inserts an item into this list.
        :param index: The index the inserted item will have in the list after insertion.
        :param item: The Value to insert.
        """
        if self.sealed:
            raise RuntimeError("This VList instance has been sealed and can thus not be modified anymore!")
        return self._items.insert(int(index), check_type(item, Value))

    @IntrinsicInstanceMethod
    def remove(self, x):
        """
        Remove the first item from the list whose value is equal to x. It raises a ValueError if there is no such item.
        :param x: The Value to remove from this list.
        """
        if self.sealed:
            raise RuntimeError("This VList instance has been sealed and can thus not be modified anymore!")
        return self._items.remove(check_type(x, Value))

    @IntrinsicInstanceMethod
    def clear(self):
        """
        Empties this list, i.e. removes all items.
        """
        if self.sealed:
            raise RuntimeError("This VList instance has been sealed and can thus not be modified anymore!")
        return self._items.clear()

    def print(self, out):
        out.write("[")
        prefix = ""
        for c in self._items:
            out.write(prefix)
            c.print(out)
            prefix = ", "
        out.write("]")

    def __repr__(self):
        return "VList({})".format(repr(list(self._items)))

    @property
    def type(self):
        return TBuiltin.list

    def hash(self):
        return len(self)

    def bequals(self, other, bijection):
        try:
            return bijection[id(self)] == id(other)
        except KeyError:
            bijection[id(self)] = id(other)
            if not (isinstance(other, VList)
                    and len(self._items) == len(other._items)):
                return False
            return all(a.bequals(b, bijection) for a, b in zip(self._items, other._items))

    def _seal(self):
        for c in self._items:
            c.seal()
        self._items = tuple(self._items)

    def clone_unsealed(self, clones=None):
        if clones is None:
            clones = {}
        try:
            return clones[id(self)]
        except KeyError:
            c = VList(self._items)
            clones[id(self)] = c
            c._items = [c.clone_unsealed(clones=clones) for c in c._items]
            return c

    def __len__(self):
        return len(self._items)

    def __iter__(self):
        return iter(self._items)

    def __getitem__(self, key):
        return self._items[int(check_type(key, Value))]

    def __setitem__(self, key, value):
        self._items[int(check_type(key, Value))] = check_type(value, Value)

    def __lt__(self, other):
        return VBool.from_bool(self._items < other._items)

    def __le__(self, other):
        return VBool.from_bool(self._items <= other._items)

    def __gt__(self, other):
        return VBool.from_bool(self._items > other._items)

    def __ge__(self, other):
        return VBool.from_bool(self._items >= other._items)


class VDict(Value):
    """
    Equivalent to Python's dicts.
    """

    def __init__(self, items=None):
        super().__init__()
        self._items = {} if items is None else {VDict._assert_key_hashable(check_type(k, Value)): check_type(v, Value) for k, v in items.items()}

    @staticmethod
    def _assert_key_hashable(key):
        """
        Asserts that the given key is hashable.
        :param key: The key to check.
        :return: The check key.
        :except VException: If the key is not hashable.
        """
        if not key.sealed:
            raise ValueError("The given key is not immutable and thus cannot be hashed!")
        return key

    @IntrinsicInstanceMethod
    def clear(self):
        """
        Empties this dictionary, i.e. removes all its entries.
        """
        if self.sealed:
            raise RuntimeError("This VDict instance has been sealed and can thus not be modified anymore!")
        self._items.clear()

    @IntrinsicInstanceMethod
    def get(self, key):
        """
        Return the value for the given key if that key is in the dictionary
        :param key: The key for which a value is to be retrieved.
        :return: The value that was retrieved.
        """
        VDict._assert_key_hashable(key)
        return self._items[check_type(key, Value)]

    @IntrinsicInstanceMethod
    def pop(self, key):
        """
        Return the value for the given key if that key is in the dictionary, and remove it from the dictionary.
        :param key: The key for which a value is to be retrieved and removed.
        :return: The value that was retrieved and removed.
        """
        if self.sealed:
            raise RuntimeError("This VDict instance has been sealed and can thus not be modified anymore!")
        VDict._assert_key_hashable(key)
        return self._items.pop(check_type(key, Value))

    @IntrinsicInstanceMethod
    def set(self, key, value):
        """
        Sets the value for the given key.
        :param key: The key for which a value is to be set.
        :param value: The value to set for the given key.
        """
        if self.sealed:
            raise RuntimeError("This VDict instance has been sealed and can thus not be modified anymore!")
        VDict._assert_key_hashable(key)
        self._items[check_type(key, Value)] = check_type(value, Value)

    def print(self, out):
        out.write("{")
        prefix = ""
        for k, v in self._items.items():
            out.write(prefix)
            k.print(out)
            out.write(": ")
            v.print(out)
            prefix = ", "
        out.write("}")

    def __repr__(self):
        return "VDict({})".format(repr(list(self._items)))

    @property
    def type(self):
        return TBuiltin.dict

    def hash(self):
        return hash(len(self))

    def bequals(self, other, bijection):
        try:
            return bijection[id(self)] == id(other)
        except KeyError:
            bijection[id(self)] = id(other)
            if not (isinstance(other, VDict)
                    and len(self._items) == len(other._items)):
                return False
            for k, v in self._items.items():
                try:
                    if not v.bequals(other._items[k], bijection):
                        return False
                except KeyError:
                    return False
            return True

    def _seal(self):
        for k, v in self._items.items():
            k.seal()
            v.seal()

    def clone_unsealed(self, clones=None):
        if clones is None:
            clones = {}
        try:
            return clones[id(self)]
        except KeyError:
            c = VDict(self._items)
            clones[id(self)] = c
            # Keys are immutable anyway and thus can remain sealed.
            c._items = {k: v.clone_unsealed(clones=clones) for k, v in c._items.items()}
            return c

    def __len__(self):
        return len(self._items)

    def __iter__(self):
        return iter(self._items)

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        self.set(key, value)


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
        super(Value, self).__init__()
        super(Exception, self).__init__(message)
        if isinstance(message, str):
            message = VStr(message)
        self._msg = check_type(message, VStr, allow_none=True)
        self._args = tuple(check_type(a, Value) for a in args)
        self._pexception = check_type(pexception, Exception, allow_none=True)

    def print(self, out):
        out.write(type(self).__name__)
        out.write("(")
        out.write(repr(self._msg))
        out.write(", ...)")

    def __repr__(self):
        return "VException({})".format(", ".join((repr(self._msg), *map(repr, self._args))))

    @property
    def type(self):
        return TBuiltin.exception

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

    def bequals(self, other, bijection):
        try:
            return bijection[id(self)] == id(other)
        except KeyError:
            bijection[id(self)] = id(other)
            if not (isinstance(other, type(self))
                    and len(self._args) == len(other._args)
                    and self._msg == other._msg
                    and self._pexception is other._pexception):
                return False
            return all(a.bequals(b, bijection) for a, b in zip(self._args, other._args))

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


class VTypeError(VException):
    """
    Raised when an inappropriate type is encountered.
    """
    @property
    def type(self):
        return TBuiltin.type_error


class VCancellationError(VException):
    """
    Raised inside a task when it is cancelled.
    """

    def __init__(self, initial):
        """
        Creates a new cancellation error.
        :param initial: Specifies if this cancellation error is to be set by TaskState.cancel, before the task had
        a chance to react to its cancellation. The first instruction to encounter an initial error will replace it
        by a non-initial one.
        """
        super().__init__("Task was cancelled!")
        self._initial = initial

    @property
    def initial(self):
        """
        Indicates if this is the initial error that was set by TaskState.cancel before the task had a chance to
        handle the error.
        """
        return self._initial

    @property
    def type(self):
        return TBuiltin.cancellation_error

    def hash(self):
        return hash(self._initial)

    def bequals(self, other, bijection):
        try:
            return bijection[id(self)] == id(other)
        except KeyError:
            bijection[id(self)] = id(other)
            if not (isinstance(other, VCancellationError)
                    and self._initial == other._initial):
                return False
            return all(a.bequals(b, bijection) for a, b in zip(self._args, other._args))

    def clone_unsealed(self, clones=None):
        if clones is None:
            clones = {}
        try:
            return clones[id(self)]
        except KeyError:
            c = VCancellationError(self._initial)
            clones[id(self)] = c
            return c


class VJumpError(VException):
    """
    Raised a control flow jump is executed.
    """
    @property
    def type(self):
        return TBuiltin.jump_error


class VReturnError(VJumpError):
    """
    Raised a return statement is executed.
    """

    def __init__(self):
        super().__init__("A procedure return is being executed!")

    @property
    def type(self):
        return TBuiltin.return_error


class VBreakError(VJumpError):
    """
    Raised a break statement is executed.
    """

    def __init__(self):
        super().__init__("An escape from a loop is being executed!")

    @property
    def type(self):
        return TBuiltin.break_error


class VContinueError(VJumpError):
    """
    Raised a continue statement is executed.
    """

    def __init__(self):
        super().__init__("A remainder of a loop body is being skipped!")

    @property
    def type(self):
        return TBuiltin.continue_exception


class VAttributeError(VException):
    """
    Raised when an attribute cannot be resolved.
    """
    @property
    def type(self):
        return TBuiltin.attribute_error


class VNamespace(Value):
    """
    A mapping from names to objects.
    """

    def __init__(self):
        """
        Creates a new empty namespace.
        """
        super().__init__()
        self._m = {}

    def print(self, out):
        out.write("namespace{")
        prefix = ""
        for k, v in self._m.items():
            out.write(prefix)
            out.write(k)
            out.write(": ")
            v.print(out)
            prefix = ", "
        out.write("}")

    @property
    def type(self):
        return TBuiltin.namespace

    def hash(self):
        return hash(len(self))

    def bequals(self, other, bijection):
        try:
            return bijection[id(self)] == id(other)
        except KeyError:
            bijection[id(self)] = id(other)
            if not (isinstance(other, VNamespace)
                    and len(self._m) == len(other._m)):
                return False
            for k, v in self._m.items():
                try:
                    if not v.bequals(other._m[k], bijection):
                        return False
                except KeyError:
                    return False
            return True

    def _seal(self):
        for v in self._m.values():
            v.seal()

    def clone_unsealed(self, clones=None):
        if clones is None:
            clones = {}
        try:
            return clones[id(self)]
        except KeyError:
            c = VNamespace()
            clones[id(self)] = c
            c._m = {k: v.clone_unsealed(clones=clones) for k, v in self._m.items()}
            return c

    def __len__(self):
        return len(self._m)

    def __iter__(self):
        return iter(self._m.items())

    def __getitem__(self, item):
        return self._m[str(check_type(item, (str, VStr)))]

    def __setitem__(self, key, value):
        if self.sealed:
            raise RuntimeError("This Namespace instance has been sealed and can thus not be modified anymore!")
        self._m[str(check_type(key, (str, VStr)))] = check_type(value, Value)


class VProcedure(Value):
    """
    Represents an executable procedure.
    """

    def __init__(self, num_args, free, entry):
        """
        Creates a new procedure.
        :param num_args: The number of arguments of this procedure.
        :param free: An iterable of values for the free variables in the procedure body.
        :param entry: A ProgramLocation that points to the entry point for this procedure.
        """
        super().__init__()
        self._num_args = check_type(num_args, int)
        self._free = check_types(free, Value)
        self._entry = check_type(entry, ProgramLocation)

    def print(self, out):
        out.write(f"Procedure({self._num_args}")
        for f in self._free:
            out.write(", ")
            f.print(out)
        out.write(", ")
        self._entry.print(out)
        out.write(")")

    @property
    def type(self):
        return TBuiltin.procedure

    @property
    def num_args(self):
        """
        The number of arguments of this procedure.
        """
        return self._num_args

    @property
    def free(self):
        """
        An iterable of values for the free variables in the procedure body.
        """
        return self._free

    @property
    def entry(self):
        """
        A ProgramLocation that points to the entry point for this procedure.
        """
        return self._entry

    def hash(self):
        return self._num_args ^ len(self._free)

    def bequals(self, other, bijection):
        try:
            return bijection[id(self)] == id(other)
        except KeyError:
            bijection[id(self)] = id(other)
            if not (isinstance(other, VProcedure)
                    and self._num_args == other._num_args
                    and len(self._free) == len(other._free)
                    and self._entry.bequals(other._entry, bijection)):
                return False
            return all(a.bequals(b, bijection) for a, b in zip(self._free, other._free))

    def _seal(self):
        self._entry.seal()
        for f in self._free:
            f.seal()

    def clone_unsealed(self, clones=None):
        if clones is None:
            clones = {}
        try:
            return clones[id(self)]
        except KeyError:
            c = VProcedure(self._num_args, self._free, self._entry)
            clones[id(self)] = c
            c._free = [f.clone_unsealed(clones=clones) for f in self._free]
            return c


class VProperty(Value):
    """
    Represents an instance property.
    """

    def __init__(self, getter, setter=None):
        """
        Creates a new procedure.
        :param getter: The getter procedure for this property.
        :param setter: Either None (in case of a readonly property), or the setter procedure for this property.
        """
        super().__init__()
        self._getter = check_type(getter, (VProcedure, IntrinsicInstanceMethod))
        self._setter = None if setter is None else check_type(setter, (VProcedure, IntrinsicInstanceMethod))

    def print(self, out):
        out.write("Property(")
        self.get_procedure.print(out)
        if self.set_procedure is not None:
            out.write(", ")
            self.set_procedure.print(out)
        out.write(")")

    @property
    def type(self):
        return TBuiltin.property

    @property
    def get_procedure(self):
        """
        The getter procedure for this property.
        It is named get_procedure to distinguish it from Python's property.getter.
        """
        return self._getter

    @property
    def set_procedure(self):
        """
        Either None (in case of a readonly property), or the setter procedure for this property.
        It is named set_procedure to distinguish it from Python's property.setter.
        """
        return self._setter

    def hash(self):
        return id(self)

    def bequals(self, other, bijection):
        return self is other

    def _seal(self):
        self._getter.seal()
        self._setter.seal()

    def clone_unsealed(self, clones=None):
        return self


class IntrinsicProperty(property, VProperty):
    """
    A property of a Python class that can also be used as an instance property at runtime.
    """

    def __init__(self, getter, setter=None):
        super().__init__(getter, setter)
        super(property, self).__init__(IntrinsicInstanceMethod(getter), None if setter is None else IntrinsicInstanceMethod(setter))

    def intrinsic_setter(self, setter):
        """
        Turns this property into one that has a setter. This method is meant to be used as a setter decorator,
        exactly like with the 'setter' attribute of ordinary Python properties.
        :param setter: The setter to be added to this property.
        :return: An IntrinsicProperty object.
        """
        return IntrinsicProperty(self.fget, setter)


class VInstance(Value):
    """
    An instance of a user-defined class.
    """

    def __init__(self, c=None, num_fields=0):
        """
        Creates a new class instance.
        :param c: The TClass instance that this object is considered an instance of.
        :param num_fields: The number of fields this instance has.
        """
        if c is None:
            c = TBuiltin.object
        super().__init__()
        self._c = c
        self._fields = [VNone.instance] * num_fields

    def print(self, out):
        out.write("Instance(")
        self.type.print(out)
        out.write(", ")
        out.write(str(id(self)))
        out.write(")")

    @property
    def type(self):
        return self._c

    def hash(self):
        return hash(self._c) ^ 42

    def bequals(self, other, bijection):
        try:
            return bijection[id(self)] == id(other)
        except KeyError:
            bijection[id(self)] = id(other)
            if not (isinstance(other, VInstance)
                    and len(self._fields) == len(other._fields)
                    and self._c.bequals(other._c, bijection)):
                return False
            return all(a.bequals(b, bijection) for a, b in zip(self._fields, other._fields))

    def _seal(self):
        self._c.seal()
        for f in self._fields:
            f.seal()

    def clone_unsealed(self, clones=None):
        if clones is None:
            clones = {}
        try:
            return clones[id(self)]
        except KeyError:
            c = VInstance(self._c, len(self._fields))
            clones[id(self)] = c
            c._c = c._c.clone_unsealed(clones=clones)
            c._fields = tuple(f.clone_unsealed(clones=clones) for f in self._fields)
            return c

    def __getitem__(self, item):
        return self._fields[check_type(item, int)]

    def __setitem__(self, key, value):
        if self.sealed:
            raise RuntimeError("This VInstance has been sealed and can thus not be modified anymore!")
        self._fields[check_type(key, int)] = check_type(value, Value)


class FutureStatus(Enum):
    UNSET = 0 # Future is in the state it was in at its initialization.
    SET = 1 # The result for the future has been set.
    FAILED = 2 # An exception for the future has been set.
    CANCELLED = 3 # The future has been cancelled.


class VFutureError(VException):
    """
    Raised when the state of a Future does not allow an operation.
    """
    @property
    def type(self):
        return TBuiltin.future_error


class VFuture(Value):
    """
    An object that represents a computation result that is not available yet.
    Its key feature is the fact that it can be awaited atomically in a guard expression.
    This makes sure that a Task can wait precisely until other tasks have made the kind of progress that it
    needs to make progress itself.
    """

    def __init__(self):
        """
        Creates a new unset future.
        """
        super().__init__()
        self._status = FutureStatus.UNSET
        self._result = VNone.instance

    def _print_status(self):
        return {FutureStatus.UNSET: "unset",
                FutureStatus.SET: "set",
                FutureStatus.FAILED: "failed",
                FutureStatus.CANCELLED: "cancelled"}[self._status]

    def print(self, out):
        out.write(f"future<{self._print_status()}>")

    def __repr__(self):
        return f"VFuture<{self._print_status()}>"

    @property
    def type(self):
        return TBuiltin.future

    def hash(self):
        return hash(self._status)

    def bequals(self, other, bijection):
        try:
            return bijection[id(self)] == id(other)
        except KeyError:
            bijection[id(self)] = id(other)
            return isinstance(other, VFuture) and self._status == other._status and self._result.bequals(other._result, bijection)

    def _seal(self):
        if self._result is not None:
            self._result.seal()

    def clone_unsealed(self, clones=None):
        if clones is None:
            clones = {}
        try:
            return clones[id(self)]
        except KeyError:
            c = VFuture()
            clones[id(self)] = c
            c._status = self._status
            if self._result is not None:
                c._result = self._result.clone_unsealed(clones=clones)
            return c

    @property
    def status(self):
        """
        The status of this future.
        """
        return self._status

    @IntrinsicProperty
    def done(self):
        """
        Indicates if a result for this future is either already available or cannot be expected anymore.
        """
        return VBool.from_bool(self._status != FutureStatus.UNSET)

    @IntrinsicInstanceMethod
    def cancel(self):
        """
        Cancels this future, i.e. notifies all stakeholders that a completion of the computation it represents cannot
        be expected anymore. If the future is not UNSET anymore, calling this method does not change state.
        :return: True, if this method actually changed the state of the future, otherwise False.
        """
        check_unsealed(self)
        if self._status == FutureStatus.UNSET:
            self._status = FutureStatus.CANCELLED
            return VBool.true
        return VBool.false

    @IntrinsicProperty
    def result(self):
        """
        The result that was set for this future.
        :return: The result that was set for this future.
        :exception: If this future is FAILED, the exception that was set for it will be *raised*.
        :except VFutureError: If this future is UNSET or CANCELLED.
        """
        if self._status == FutureStatus.UNSET:
            raise VFutureError("No result can be obtained for this future, because none has been set yet!")
        elif self._status == FutureStatus.SET:
            return self._result
        elif self._status == FutureStatus.CANCELLED:
            raise VFutureError("Cannot retrieve the result for a future that has been cancelled!")
        elif self._status == FutureStatus.FAILED:
            raise self._result
        else:
            raise NotImplementedError(f"Handling {self._status} as not been implemented!")

    @result.intrinsic_setter
    def result(self, value):
        """
        Sets the result of this future and marks it as done.
        :param value: The result value to set.
        :exception VFutureError: If the future is already SET.
        :exception SealedException: If this future has been sealed.
        :exception TypeError: If the given value is not a proper Value.
        """
        check_unsealed(self)
        if self._status == FutureStatus.SET:
            raise VFutureError("This future has already been set!")
        self._result = check_type(value, Value)
        self._status = FutureStatus.SET

    @IntrinsicProperty
    def exception(self):
        """
        The exception that was set on this future.
        :return: The VException that as set for this future. If a proper result was set, None is returned.
        :except VFutureError: If this future is UNSET or CANCELLED.
        """
        if self._status == FutureStatus.UNSET:
            raise VFutureError("Cannot retrieve the exception for a future that is still unset!")
        elif self._status == FutureStatus.SET:
            return None
        elif self._status == FutureStatus.CANCELLED:
            raise VFutureError("Cannot retrieve the exception for a future that has been cancelled!")
        elif self._status == FutureStatus.FAILED:
            return self._result
        else:
            raise NotImplementedError(f"Handling {self._status} as not been implemented!")

    @exception.intrinsic_setter
    def exception(self, value):
        """
        Sets an exception for this future.
        :param value: The VException value to set.
        :exception VFutureError: If the future is already SET.
        :exception SealedException: If this future has been sealed.
        :exception TypeError: If the given value is not a proper VException.
        """
        check_unsealed(self)
        if self._status == FutureStatus.SET:
            raise VFutureError("This future has already been set!")
        self._result = check_type(value, VException)
        self._status = FutureStatus.FAILED


from .types import TBuiltin
from ..tasks.program import ProgramLocation
