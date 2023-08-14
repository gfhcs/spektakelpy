from engine.intrinsic import IntrinsicInstanceMethod, IntrinsicProcedure
from util import check_type
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

    def equals(self, other):
        return isinstance(other, VNone)

    def _seal(self):
        pass

    def clone_unsealed(self, clones=None):
        return self

    def __str__(self):
        return "None"

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


class VInt(Value):
    """
    Equivalent to Python's int.
    """

    def __init__(self, value=0):
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

    def __init__(self, value=0.0):
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
        return isinstance(other, VStr) and self._value == other._value

    def _seal(self):
        pass

    def clone_unsealed(self, clones=None):
        return self

    def __contains__(self, item):
        return str(item) in self._value

    def __lt__(self, other):
        return VBool.from_bool(self._value < other._value)

    def __le__(self, other):
        return VBool.from_bool(self._value <= other._value)

    def __gt__(self, other):
        return VBool.from_bool(self._value > other._value)

    def __ge__(self, other):
        return VBool.from_bool(self._value >= other._value)


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

    def __str__(self):
        return str(self._items)

    def __repr__(self):
        return "VList({})".format(repr(list(self._items)))

    @property
    def type(self):
        return TBuiltin.list

    def hash(self):
        return hash(tuple(self._items))

    def equals(self, other):
        return isinstance(other, VList) and self._items == other._items

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
        self._items = {} if items is None else {check_type(k, Value): check_type(v, Value) for k, v in items.items()}

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
        if self.sealed:
            raise RuntimeError("This VDict instance has been sealed and can thus not be modified anymore!")
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
        self._items[check_type(key, Value)] = check_type(value, Value)

    def __str__(self):
        return str(self._items)

    def __repr__(self):
        return "VDict({})".format(repr(list(self._items)))

    @property
    def type(self):
        return TBuiltin.dict

    def hash(self):
        return hash(len(self))

    def equals(self, other):
        if not isinstance(other, VDict) or len(self) != len(other):
            return False
        for k, v in self._items.items():
            if other._items[k] != v:
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
            c._items = {k.clone_unsealed(clones=clones): v.clone_unsealed(clones=clones) for k, v in c._items.items()}
            return c

    def __len__(self):
        return len(self._items)

    def __iter__(self):
        return iter(self._items)

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        self.set(key, value)


class VException(Value):
    """
    The base type for all exceptions.
    """

    def __init__(self, message=None, *args, pexception=None):
        """
        Creates a new exception
        :param message: The message for this exception.
        :param args: Additional constructor arguments that annotate the exception.
        :param pexception: An underlying Python exception, if it caused the exception to be created.
        """
        super().__init__()
        self._msg = check_type(message, str, allow_none=True)
        self._args = tuple(check_type(a, Value) for a in args)
        self._pexception = check_type(pexception, Exception, allow_none=True)

    def __str__(self):
        return str("{}: {}".format(type(self), self._msg))

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

    def _seal(self):
        for a in self._args:
            a.seal()

    def hash(self):
        return hash((self._msg, *self._args))

    def equals(self, other):
        return isinstance(other, type(self)) and (self._msg, *self._args) == (other._msg, *other._args) and self._pexception is other._pexception

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


class VJumpError(VException):
    """
    Raised a control flow jump is executed.
    """
    @property
    def type(self):
        return TBuiltin.jump_exception


class VReturnError(VJumpError):
    """
    Raised a return statement is executed.
    """
    @property
    def type(self):
        return TBuiltin.return_error


class VBreakError(VJumpError):
    """
    Raised a break statement is executed.
    """
    @property
    def type(self):
        return TBuiltin.break_error


class VContinueError(VJumpError):
    """
    Raised a continue statement is executed.
    """
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

    @property
    def type(self):
        return TBuiltin.namespace

    def hash(self):
        return hash(len(self))

    def equals(self, other):
        if not isinstance(other, VNamespace) or len(self) != len(other):
            return False
        for k, v in self._m.items():
            if other._m[k] != v:
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

    def __init__(self, num_args, entry):
        """
        Creates a new procedure.
        :param num_args: The number of arguments of this procedure.
        :param entry: Either a ProgramLocation that points to the entry point for this procedure, or an IntrinsicProcedure,
                      or a StackProgram.
        """
        super().__init__()
        self._num_args = check_type(num_args, int)

        if isinstance(entry, (ProgramLocation, IntrinsicProcedure, StackProgram)):
            self._entry = entry
        else:
            raise TypeError("The given entry object is neither a ProgramLocation nor an IntrinsicProcedure!")

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
    def entry(self):
        """
        Either a ProgramLocation or an IntrinsicProcedure, or a StackProgram object.
        """
        return self._entry

    def hash(self):
        return hash(self._entry)

    def equals(self, other):
        return id(self) == id(other)

    def _seal(self):
        self._entry.seal()

    def clone_unsealed(self, clones=None):
        return self


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
        self._getter = check_type(getter, VProcedure)
        self._setter = None if setter is None else check_type(setter, VProcedure)

    @property
    def type(self):
        return TBuiltin.property

    @property
    def getter(self):
        """
        The getter procedure for this property.
        """
        return self._getter

    @property
    def setter(self):
        """
        Either None (in case of a readonly property), or the setter procedure for this property.
        """
        return self._setter

    def hash(self):
        return hash((self._getter, self._setter))

    def equals(self, other):
        return id(self) == id(other)

    def _seal(self):
        self._getter.seal()
        self._setter.seal()

    def clone_unsealed(self, clones=None):
        return self


class VModule(Value):
    """
    Represents a module at runtime.
    """

    def __init__(self, namespace):
        """
        Creates a new module.
        :param namespace: The namespace defining this module.
        """
        super().__init__()
        self._ns = namespace

    @property
    def type(self):
        return TBuiltin.module

    def hash(self):
        return hash(self._ns)

    def equals(self, other):
        return self._ns == other._ns

    def _seal(self):
        self._ns.seal()

    def clone_unsealed(self, clones=None):
        if clones is None:
            clones = {}
        try:
            return clones[id(self)]
        except KeyError:
            c = VModule(self._ns)
            clones[id(self)] = c
            c._ns = c._ns.clone_unsealed(clones=clones)
            return c


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

    @property
    def type(self):
        return self._c

    def hash(self):
        return hash((self._c, *self._fields))

    def equals(self, other):
        return isinstance(other, VInstance) and self._c == other._c and tuple(self._fields) == tuple(other._fields)

    def _seal(self):
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

from .types import TBuiltin
from ..tasks.instructions import ProgramLocation, StackProgram
