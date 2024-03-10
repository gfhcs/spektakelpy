from engine.core.data import VBool, VNone, VStr
from engine.core.intrinsic import intrinsic, intrinsic_constructor
from engine.core.type import Type
from engine.core.value import Value
from lang.spek.data.builtin import builtin
from util import check_type
from util.immutable import check_unsealed


@builtin()
@intrinsic("tuple", [Type.get_instance_object()])
class VTuple(Value):
    """
    Equivalent to Python's tuples.
    """

    def __init__(self, *components):
        super().__init__()
        self._comps = tuple(check_type(c, Value) for c in components)

    @intrinsic_constructor()
    @classmethod
    def convert(cls, iterable):
        assert issubclass(cls, VTuple)
        return cls(*iterable)

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
        return VTuple.machine_type

    def hash(self):
        return len(self._comps)

    def equals(self, other):
        return self is other

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

    def cequals(self, other):
        return (isinstance(other, VTuple)
                and len(self._comps) == len(other._comps)
                and all(a.equals(b) for a, b in zip(self._comps, other._comps)))

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


@builtin()
@intrinsic("list", [Type.get_instance_object()])
class VList(Value):
    """
    Equivalent to Python's lists.
    """

    def __init__(self, items=None):
        super().__init__()
        self._items = [] if items is None else [check_type(x, Value) for x in items]

    @intrinsic()
    def append(self, item):
        """
        Appends an item to this list.
        :param item: The item to append.
        """
        if self.sealed:
            raise RuntimeError("This VList instance has been sealed and can thus not be modified anymore!")
        return self._items.append(check_type(item, Value))

    @intrinsic()
    def pop(self, index):
        """
        Pops an item from this list.
        :param index: The index of the item to pop.
        :return: The popped item.
        """
        if self.sealed:
            raise RuntimeError("This VList instance has been sealed and can thus not be modified anymore!")
        return self._items.pop(int(index))

    @intrinsic()
    def insert(self, index, item):
        """
        Inserts an item into this list.
        :param index: The index the inserted item will have in the list after insertion.
        :param item: The Value to insert.
        """
        if self.sealed:
            raise RuntimeError("This VList instance has been sealed and can thus not be modified anymore!")
        return self._items.insert(int(index), check_type(item, Value))

    @intrinsic()
    def remove(self, x):
        """
        Remove the first item from the list whose value is equal to x. It raises a ValueError if there is no such item.
        :param x: The Value to remove from this list.
        """
        if self.sealed:
            raise RuntimeError("This VList instance has been sealed and can thus not be modified anymore!")
        return self._items.remove(check_type(x, Value))

    @intrinsic()
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
        return VList.machine_type

    def hash(self):
        return len(self)

    def equals(self, other):
        return self is other

    def bequals(self, other, bijection):
        try:
            return bijection[id(self)] == id(other)
        except KeyError:
            bijection[id(self)] = id(other)
            if not (isinstance(other, VList)
                    and len(self._items) == len(other._items)):
                return False
            return all(a.bequals(b, bijection) for a, b in zip(self._items, other._items))

    def cequals(self, other):
        return (isinstance(other, VList)
                and len(self._items) == len(other._items)
                and all(a.cbequals(b) for a, b in zip(self._items, other._items)))

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


@builtin()
@intrinsic("dict", [Type.get_instance_object()])
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

    @intrinsic()
    def clear(self):
        """
        Empties this dictionary, i.e. removes all its entries.
        """
        if self.sealed:
            raise RuntimeError("This VDict instance has been sealed and can thus not be modified anymore!")
        self._items.clear()

    @intrinsic()
    def get(self, key):
        """
        Return the value for the given key if that key is in the dictionary
        :param key: The key for which a value is to be retrieved.
        :return: The value that was retrieved.
        """
        VDict._assert_key_hashable(key)
        return self._items[check_type(key, Value)]

    @intrinsic()
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

    @intrinsic()
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
        return VDict.machine_type

    def hash(self):
        return hash(len(self))

    def equals(self, other):
        return self is other

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

    def cequals(self, other):
        if not (isinstance(other, VDict)
                and len(self._items) == len(other._items)):
            return False
        for k, v in self._items.items():
            try:
                if not v.cequals(other._items[k]):
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


@intrinsic("namespace", [Type.get_instance_object()])
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
        return VNamespace.machine_type

    def hash(self):
        return hash(len(self))

    def equals(self, other):
        return self is other

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

    def cequals(self, other):
        return self.equals(other)

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


class VInstance(Value):
    """
    An instance of a user-defined class.
    """

    def __init__(self, type, num_fields=0):
        """
        Creates a new class instance.
        :param c: The Type instance that this object is considered an instance of.
        :param num_fields: The number of fields this instance has.
        """
        super().__init__()
        self._type = type
        self._fields = [VNone.instance] * num_fields

    def print(self, out):
        out.write("Instance(")
        self.type.print(out)
        out.write(", ")
        out.write(str(id(self)))
        out.write(")")

    @property
    def type(self):
        return self._type

    def hash(self):
        return hash(self._type) ^ 42

    def equals(self, other):
        return self is other

    def bequals(self, other, bijection):
        try:
            return bijection[id(self)] == id(other)
        except KeyError:
            bijection[id(self)] = id(other)
            if not (isinstance(other, VInstance)
                    and len(self._fields) == len(other._fields)
                    and self._type.bequals(other._type, bijection)):
                return False
            return all(a.bequals(b, bijection) for a, b in zip(self._fields, other._fields))

    def cequals(self, other):
        return self.equals(other)

    def _seal(self):
        self._type.seal()
        for f in self._fields:
            f.seal()

    def clone_unsealed(self, clones=None):
        if clones is None:
            clones = {}
        try:
            return clones[id(self)]
        except KeyError:
            c = VInstance(self._type, len(self._fields))
            clones[id(self)] = c
            c._type = c._type.clone_unsealed(clones=clones)
            c._fields = tuple(f.clone_unsealed(clones=clones) for f in self._fields)
            return c

    def __getitem__(self, item):
        return self._fields[check_type(item, int)]

    def __setitem__(self, key, value):
        check_unsealed(self)
        self._fields[check_type(key, int)] = check_type(value, Value)


