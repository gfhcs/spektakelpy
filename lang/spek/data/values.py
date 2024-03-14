from engine.core.atomic import type_object
from engine.core.intrinsic import intrinsic_type, intrinsic_init, intrinsic_member
from engine.core.primitive import VBool
from engine.core.value import Value
from lang.spek.data.builtin import builtin
from lang.spek.data.exceptions import VKeyError, VIndexError
from util import check_type


@builtin()
@intrinsic_type("tuple", [type_object])
class VTuple(Value):
    """
    Equivalent to Python's tuples.
    """

    @intrinsic_init()
    def __init__(self, components):
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
        return VTuple.intrinsic_type

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
            c = VTuple(self._comps)
            clones[id(self)] = c
            c._comps = tuple(c.clone_unsealed(clones=clones) for c in self._comps)
            return c

    def __len__(self):
        return len(self._comps)

    def __iter__(self):
        return iter(self._comps)

    def __contains__(self, item):
        return item in self._comps

    def __getitem__(self, key):
        try:
            return self._comps[int(check_type(key, Value))]
        except IndexError as iex:
            raise VIndexError(str(iex))

    def __lt__(self, other):
        return VBool(self._comps < other._comps)

    def __le__(self, other):
        return VBool(self._comps <= other._comps)

    def __gt__(self, other):
        return VBool(self._comps > other._comps)

    def __ge__(self, other):
        return VBool(self._comps >= other._comps)

    def __add__(self, other):
        return self._comps.__add__(tuple(other))


@builtin()
@intrinsic_type("list", [type_object])
class VList(Value):
    """
    Equivalent to Python's lists.
    """

    def __init__(self, items=None):
        super().__init__()
        self._items = [] if items is None else [check_type(x, Value) for x in items]

    @intrinsic_member()
    def append(self, item):
        """
        Appends an item to this list.
        :param item: The item to append.
        """
        if self.sealed:
            raise RuntimeError("This VList instance has been sealed and can thus not be modified anymore!")
        return self._items.append(check_type(item, Value))

    @intrinsic_member()
    def pop(self, index):
        """
        Pops an item from this list.
        :param index: The index of the item to pop.
        :return: The popped item.
        """
        if self.sealed:
            raise RuntimeError("This VList instance has been sealed and can thus not be modified anymore!")
        return self._items.pop(int(index))

    @intrinsic_member()
    def insert(self, index, item):
        """
        Inserts an item into this list.
        :param index: The index the inserted item will have in the list after insertion.
        :param item: The Value to insert.
        """
        if self.sealed:
            raise RuntimeError("This VList instance has been sealed and can thus not be modified anymore!")
        return self._items.insert(int(index), check_type(item, Value))

    @intrinsic_member()
    def remove(self, x):
        """
        Remove the first item from the list whose value is equal to x. It raises a ValueError if there is no such item.
        :param x: The Value to remove from this list.
        """
        if self.sealed:
            raise RuntimeError("This VList instance has been sealed and can thus not be modified anymore!")
        return self._items.remove(check_type(x, Value))

    @intrinsic_member()
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
        return VList.intrinsic_type

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
        return VBool(self._items < other._items)

    def __le__(self, other):
        return VBool(self._items <= other._items)

    def __gt__(self, other):
        return VBool(self._items > other._items)

    def __ge__(self, other):
        return VBool(self._items >= other._items)


@builtin()
@intrinsic_type("dict", [type_object])
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

    def items(self):
        return self._items.items()

    @intrinsic_member()
    def clear(self):
        """
        Empties this dictionary, i.e. removes all its entries.
        """
        if self.sealed:
            raise RuntimeError("This VDict instance has been sealed and can thus not be modified anymore!")
        self._items.clear()

    @intrinsic_member()
    def get(self, key):
        """
        Return the value for the given key if that key is in the dictionary
        :param key: The key for which a value is to be retrieved.
        :return: The value that was retrieved.
        """
        VDict._assert_key_hashable(key)
        try:
            return self._items[check_type(key, Value)]
        except KeyError as kex:
            raise VKeyError(str(kex))

    @intrinsic_member()
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

    @intrinsic_member()
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
        return VDict.intrinsic_type

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
