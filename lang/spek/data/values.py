import abc

from engine.core.atomic import type_object, VObject
from engine.core.data import VBool, VIndexError, VKeyError, VInt, VIndexingIterator, VIterator, VRuntimeError
from engine.core.intrinsic import intrinsic_type, intrinsic_member
from engine.core.value import Value
from engine.stack.exceptions import VTypeError, unhashable
from lang.spek.data.builtin import builtin
from util import check_type
from util.immutable import check_unsealed


@builtin()
@intrinsic_type("tuple", [type_object])
class VTuple(Value):
    """
    Equivalent to Python's tuples.
    """

    @intrinsic_member()
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
        return f"VTuple({', '.join(self._comps)}"

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

    def chash(self):
        return hash(c.chash() for c in self)

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
        return VIndexingIterator(self)

    def __contains__(self, item):
        return any(c.cequals(item) for c in self)

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

    def __mul__(self, other):
        return self._comps.__mul__(other)


@builtin()
@intrinsic_type("range", [type_object])
class VRange(Value):
    """
    Equivalent to Python's range type.
    """

    @intrinsic_member()
    def __init__(self, stop):
        super().__init__()
        self._stop = check_type(stop, VInt)

    def print(self, out):
        out.write(f"range({self._stop})")

    @property
    def type(self):
        return VRange.intrinsic_type

    def hash(self):
        return hash(self._stop)

    def equals(self, other):
        return self is other

    def bequals(self, other, bijection):
        try:
            return bijection[id(self)] == id(other)
        except KeyError:
            bijection[id(self)] = id(other)
            return isinstance(other, VRange) and self._stop == other._stop

    def cequals(self, other):
        return isinstance(other, VRange) and self._stop == other._stop

    def chash(self):
        return hash(self._stop)

    def _seal(self):
        pass

    def clone_unsealed(self, clones=None):
        return self

    def __len__(self):
        return self._stop

    def __iter__(self):
        return VIndexingIterator(self)

    def __contains__(self, item):
        return isinstance(item, VInt) and 0 <= item < self._stop

    def __getitem__(self, index):
        if not isinstance(index, VInt):
            raise VTypeError("range indices must be integers!")
        if not (0 <= index < self._stop):
            raise VIndexError("range object index out of range")
        return index


class TokenizedMutable(Value):
    """
    A Value that each time it is modified will also modify a public mutation token.
    """

    @property
    @abc.abstractmethod
    def mtoken(self):
        """
        The current mutation token. Whenever this object is modified, this token changes.
        :return: A Value.
        """
        pass


@intrinsic_type("mutable_indexing_iterator", [type_object])
class VMutableIterator(VIterator):
    """
    An indexing iterator over a mutable sequence. This iterator becomes unusable when the sequence is modified.
    """

    def __init__(self, core, iterable=None):
        """
        Wraps a VIterator over a MutableIterable as a VMutableIterator.
        :param core: A VIterator the iterable of which inherits TokenizedMutable.
        :param iterable: The iterable that this iterator is supposed to belong to. If omitted, the iterator
                         of the core will be used.
        """
        if iterable is None:
            iterable = core.iterable
        super().__init__(check_type(iterable, TokenizedMutable))
        self._core = core
        self._mtoken = iterable.mtoken

    @property
    def type(self):
        return VMutableIterator.intrinsic_type

    def bequals(self, other, bijection):
        try:
            return bijection[id(self)] == id(other)
        except KeyError:
            bijection[id(self)] = id(other)
            return (isinstance(other, VMutableIterator)
                    and self._mtoken.bequals(other._mtoken, bijection)
                    and self._core.bequals(other._core, bijection)
                    and self.iterable.bequals(other.iterable, bijection))

    def clone_unsealed(self, clones=None):
        if clones is None:
            clones = {}
        try:
            return clones[id(self)]
        except KeyError:
            c = VMutableIterator(self._core.clone_unsealed(clones=clones), iterable=self.iterable.clone_unsealed(clones=clones))
            clones[id(self)] = c
            c._mtoken = self._mtoken.clone_unsealed(clones=clones)
            return c

    def _seal(self):
        self.iterable.seal()
        self._core.seal()
        self._mtoken.seal()

    def sequals(self, other):
        raise NotImplementedError()

    def copy_unsealed(self):
        raise NotImplementedError()

    def print(self, out):
        out.write("mutable_iterator(")
        self._core.print(out)
        out.write(", ")
        self._mtoken.print(out)
        out.write(")")

    @intrinsic_member("__next__")
    def next(self):
        if not self._mtoken.cequals(self.iterable.mtoken):
            raise VRuntimeError("The iterable underlying this iterator has been modified!")
        return self._core.next()


@builtin()
@intrinsic_type("list", [type_object])
class VList(TokenizedMutable):
    """
    Equivalent to Python's lists.
    """

    @intrinsic_member()
    def __init__(self, elements):
        """
        Constructs a new VList.
        :param elements: An iterable of Value objects that should form the elements of the list.
        """
        super().__init__()
        self._items = [] if elements is None else [check_type(x, Value) for x in elements]
        self._mtoken = VObject()

    @property
    def mtoken(self):
        return self._mtoken

    def _mutate(self):
        check_unsealed(self)
        self._mtoken = VObject()

    @intrinsic_member()
    def append(self, item):
        """
        Appends an item to this list.
        :param item: The item to append.
        """
        self._mutate()
        return self._items.append(check_type(item, Value))

    @intrinsic_member()
    def pop(self, index):
        """
        Pops an item from this list.
        :param index: The index of the item to pop.
        :return: The popped item.
        """
        self._mutate()
        return self._items.pop(int(index))

    @intrinsic_member()
    def extend(self, iterable):
        """
        Exends this list by an iterable of further elements.
        :param iterable: An iterable of Values.
        """
        self._mutate()
        return self._items.extend(check_type(x, Value) for x in iterable)

    @intrinsic_member()
    def insert(self, index, item):
        """
        Inserts an item into this list.
        :param index: The index the inserted item will have in the list after insertion.
        :param item: The Value to insert.
        """
        self._mutate()
        return self._items.insert(int(index), check_type(item, Value))

    @intrinsic_member()
    def remove(self, x):
        """
        Remove the first item from the list whose value is equal to x. It raises a ValueError if there is no such item.
        :param x: The Value to remove from this list.
        """
        self._mutate()
        return self._items.remove(check_type(x, Value))

    @intrinsic_member()
    def clear(self):
        """
        Empties this list, i.e. removes all items.
        """
        self._mutate()
        return self._items.clear()

    @intrinsic_member()
    def sort(self):
        """
        Sorts this list stably in-place.
        """
        self._mutate()
        self._items.sort()

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
                    and len(self._items) == len(other._items)
                    and self._mtoken.bequals(other._mtoken, bijection)):
                return False
            return all(a.bequals(b, bijection) for a, b in zip(self._items, other._items))

    def cequals(self, other):
        return (isinstance(other, VList)
                and len(self._items) == len(other._items)
                and all(a.cbequals(b) for a, b in zip(self._items, other._items)))

    def chash(self):
        return unhashable(self)

    def _seal(self):
        self._mtoken.seal()
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
            c._mtoken = self._mtoken.clone_unsealed(clones=clones)
            c._items = [c.clone_unsealed(clones=clones) for c in c._items]
            return c

    def __len__(self):
        return len(self._items)

    def __iter__(self):
        return VMutableIterator(VIndexingIterator(self))

    def __getitem__(self, key):
        try:
            return self._items[int(check_type(key, Value))]
        except IndexError as iex:
            raise VIndexError(str(iex))

    def __setitem__(self, key, value):
        self._mutate()
        self._items[int(check_type(key, Value))] = check_type(value, Value)

    def __add__(self, other):
        if not isinstance(other, VList):
            raise VTypeError(f"Can only concatenate list (not \"{other.type}\" to list")
        return VList([*self, *other])

    def __mul__(self, other):
        if not isinstance(other, int):
            raise VTypeError(f"Can't multiply sequence by non-int of type '{other.type}'")
        return VList(list(self) * other)

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
class VDict(TokenizedMutable):
    """
    Equivalent to Python's dicts.
    """

    class Key:
        """
        Wraps a Value as a Python object that is hashable according to Value.chash.
        """

        def __init__(self, x):
            self._x = check_type(x, Value)

        def __str__(self):
            return str(self._x)

        def __repr__(self):
            return repr(self._x)

        def __hash__(self):
            return self._x.chash()

        def __eq__(self, other):
            return isinstance(other, VDict.Key) and self._x.cequals(other._x)

        def __ne__(self, other):
            return self.__eq__(other)

        @property
        def wrapped(self):
            return self._x

    @intrinsic_member()
    def __init__(self, items):
        """
        Constructs a new VDict.
        :param items: Either a VDict that is to be copied, or an iterable of key-value pairs that is to be turned
                      into a new VDict.
        """
        super().__init__()
        if isinstance(items, VDict):
            self._items = dict(items.items_python())
        elif isinstance(items, dict):
            self._items = {VDict.Key(k): check_type(v, Value) for k, v in items.items()}
        else:
            self._items = {VDict.Key(k): check_type(v, Value) for k, v in items}

        self._mtoken = VObject()

    @property
    def mtoken(self):
        return self._mtoken

    def _mutate(self):
        check_unsealed(self)
        self._mtoken = VObject()

    def keys_python(self):
        """
        A Python view on the keys of this VDict.
        """
        return self._items.keys()

    @intrinsic_member()
    def keys(self):
        return VKeysView(self)

    def values_python(self):
        """
        A Python view on the values of this VDict.
        """
        return self._items.values()

    @intrinsic_member()
    def values(self):
        return VValuesView(self)

    def items_python(self):
        """
        A Python view on the items of this VDict.
        """
        return self._items.items()

    @intrinsic_member()
    def items(self):
        return VItemsView(self)

    @intrinsic_member()
    def clear(self):
        """
        Empties this dictionary, i.e. removes all its entries.
        """
        self._mutate()
        self._items.clear()

    @intrinsic_member()
    def pop(self, key):
        """
        Return the value for the given key if that key is in the dictionary, and remove it from the dictionary.
        :param key: The key for which a value is to be retrieved and removed.
        :return: The value that was retrieved and removed.
        """
        self._mutate()
        return self._items.pop(VDict.Key(key))

    @intrinsic_member()
    def update(self, other):
        """
        Update this VDict with the key/value pairs from other, overwriting existing keys.
        :param other: Either a VDict or an iterable of key/value pairs.
        """
        self._mutate()
        if isinstance(other, VDict):
            self._items.update(other._items)
        else:
            self._items.update((VDict.Key(k), check_type(v, Value)) for k, v in (other.items() if isinstance(other, dict) else other))

    def print(self, out):
        out.write("{")
        prefix = ""
        for k, v in self._items.items():
            out.write(prefix)
            k.wrapped.print(out)
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
                    and len(self._items) == len(other._items)
                    and self._mtoken.bequals(other._mtoken, bijection)):
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

    def chash(self):
        return unhashable(self)

    def _seal(self):
        self._mtoken.seal()
        for k, v in self._items.items():
            k.wrapped.seal()
            v.seal()

    def clone_unsealed(self, clones=None):
        if clones is None:
            clones = {}
        try:
            return clones[id(self)]
        except KeyError:
            c = VDict(self)
            clones[id(self)] = c
            c._mtoken = self._mtoken.clone_unsealed(clones=clones)
            c._items = {VDict.Key(k.wrapped.clone_unsealed(clones=clones)): v.clone_unsealed(clones=clones) for k, v in c._items.items()}
            return c

    def __len__(self):
        return len(self._items)

    def __iter__(self):
        return iter(self.keys())

    def __contains__(self, key):
        return VDict.Key(key) in self._items

    def __getitem__(self, key):
        try:
            return self._items[VDict.Key(key)]
        except KeyError as kex:
            raise VKeyError(str(key))

    def __setitem__(self, key, value):
        self._mutate()
        self._items[VDict.Key(key)] = check_type(value, Value)

    def __ior__(self, other):
        self.update(other)

    def __or__(self, other):
        c = VDict(self)
        c.update(other)
        return c


@builtin()
@intrinsic_type("dictview", [type_object])
class VDictView(TokenizedMutable):
    """
    A readonly view of a VDict.
    """

    def __init__(self, d):
        """
        Creates a new view of a VDict.
        :param d: The VDict object that this view is for.
        """
        super().__init__()
        self._d = check_type(d, VDict)

    @property
    def mtoken(self):
        return self._d.mtoken

    @property
    def mapping(self):
        """
        The VDict that this view gives readonly access to.
        """
        return self._d

    def print(self, out):
        out.write(type(self).__name__)
        out.write("(")
        self._d.print(out)
        out.write(")")

    @property
    def type(self):
        return type(self).intrinsic_type

    def hash(self):
        return hash(self._d)

    def equals(self, other):
        return self is other

    def bequals(self, other, bijection):
        try:
            return bijection[id(self)] == id(other)
        except KeyError:
            bijection[id(self)] = id(other)
            return isinstance(other, type(self)) and self._d.bequals(other._d, bijection)

    def cequals(self, other):
        return isinstance(other, type(self)) and self._d is other._d

    def chash(self):
        return unhashable(self)

    def _seal(self):
        self._d.seal()

    def clone_unsealed(self, clones=None):
        if clones is None:
            clones = {}
        try:
            return clones[id(self)]
        except KeyError:
            c = type(self)(self._d)
            clones[id(self)] = c
            c._d = self._d.clone_unsealed(clones=clones)
            return c

    def __len__(self):
        return len(self._d)

    @abc.abstractmethod
    def iter(self):
        """
        Returns a Python iterable for this view.
        """
        pass

    @abc.abstractmethod
    def contains(self, element):
        """
        Decides if this view contains the given element.
        :param element: A Value object.
        :return: A bool value.
        """
        pass

    def __iter__(self):
        return self.iter()

    def __contains__(self, x):
        return self.contains(x)


@builtin()
@intrinsic_type("dictkeys")
class VKeysView(VDictView):
    """
    A view on the keys of a VDict.
    """

    def iter(self):
        return VMutableIterator(iter(VTuple(k.wrapped for k in self.mapping.keys_python())), iterable=self)

    def contains(self, element):
        return element in self.mapping


@builtin()
@intrinsic_type("dictvalues")
class VValuesView(VDictView):
    """
    A view on the values of a VDict.
    """

    def iter(self):
        return VMutableIterator(iter(VTuple(self.mapping.values_python())), iterable=self)

    def contains(self, x):
        return any(x.cequals(v) for v in self.mapping.values_python())


@builtin()
@intrinsic_type("dictitems")
class VItemsView(VDictView):
    """
    A view on the items of a VDict.
    """

    def iter(self):
        return VMutableIterator(iter(VTuple(VTuple((k.wrapped, v)) for k, v in self.mapping.items_python())), iterable=self)

    def contains(self, x):
        k, v = x
        try:
            found = self.mapping[k]
        except VKeyError:
            return False
        else:
            return found.cequals(v)
