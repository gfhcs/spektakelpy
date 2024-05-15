from abc import ABC

from engine.core.atomic import type_type, AtomicType
from engine.core.finite import FiniteValue
from engine.core.none import value_none
from engine.core.type import Type, merge_linear, linearization
from engine.core.value import Value
from util import check_type
from util.immutable import check_unsealed


class FieldIndex(FiniteValue):
    """
    An index into the fields of a compound value.
    """

    def __init__(self, idx):
        # __new__ takes care of idx.
        super().__init__()

    def __int__(self):
        return self.instance_index

    def __add__(self, other):
        return FieldIndex(int(self) + int(other))

    def __radd__(self, other):
        return FieldIndex(int(self) + int(other))

    @property
    def value(self):
        """
        The nonnegative integer represented by this object.
        """
        return self.instance_index

    @property
    def type(self):
        raise NotImplementedError("The type of a field index should never be needed.")

    def print(self, out):
        out.write(f"{self.instance_index}")


class CompoundType(Type, ABC):
    """
    A type the instances of which consist of tuples of other type instances.
    """

    def __init__(self, name, bases, direct_field_names, direct_members):
        """
        Creates a new type.
        :param name: The name of this type.
        :param bases: A tuple of Type objects that the new type inherits from.
        :param direct_members: A mapping from names to Values that defines the *direct* members of this type.
        :param direct_field_names: The names of the direct fields of instances of this type, i.e. those fields that
                                   are not inherited from base classes.
        """

        direct_members = dict(direct_members)

        offsets = [0]
        offset = 0
        for n in direct_field_names:
            direct_members[n] = FieldIndex(offset)
            offset += 1

        for idx, t in enumerate(merge_linear([*(list(linearization(b)) for b in bases), list(bases)])):
            offsets.append(offset)
            if isinstance(t, AtomicType):
                direct_members[idx + 1] = FieldIndex(offset)
                offset += 1
            elif isinstance(t, CompoundType):
                for n, member in t.direct_members.items():
                    if isinstance(member, FieldIndex):
                        offset += 1
            else:
                raise TypeError(f"Compound types can only inherit from atomic types and other compound types, not from {type(t)}!")
        super().__init__(name, bases, direct_members)
        self._size = offset
        self._offsets = offsets

    def get_atomic_base_field(self, types):
        """
        Given an iterable of atomic types that self may be an instance of, retrieves a field index under which
        an instance of one of those atomic types is stored in instances of self, if that atomic type is the first
        in self.type.mro that self actually is an instance of.
        :param types: An iterable of AtomicTypes that self may be an instance of.
        :return: A FieldIndex.
        :exception ValueError: If self is not an instance of any of the given AtomicTypes.
        """
        for t in types:
            if not isinstance(t, AtomicType):
                raise TypeError(f"CompoundType.get_atomic_base_field only accepts AtomicTypes, not {type(t)}!")

        for idx, base in enumerate(self.mro):
            for t in types:
                if base is t:
                    return self.direct_members[idx]

        raise ValueError(f"{self} is not an instance of any of the types in {types}!")

    @property
    def type(self):
        return type_type

    @property
    def size(self):
        """
        The number of private data fields in the instances of this type.
        :return: An int.
        """
        return self._size

    def get_offset(self, t):
        """
        Computes the offset at which the *direct* fields of the given super type begin in the instances of this type.
        :param t: A super type of this type. May even be this type itself.
        :return: An int.
        """
        for offset, base in zip(self._offsets, self.mro):
            if base.cequals(t):
                return offset

    def new(self, *args):
        instance = VCompound(self)
        for idx, t in enumerate(self.mro):
            if isinstance(t, AtomicType):
                instance[self.direct_members[idx]] = t.new(*args)
        return instance

    def resolve_member(self, name, ctype=None):
        if ctype is not None:
            try:
                m = ctype.direct_members[name]
                if isinstance(m, FieldIndex):
                    for t, offset in zip(self.mro, self._offsets):
                        if t.cequals(ctype):
                            return offset + m
            except KeyError:
                pass

        for t in self.mro:
            try:
                m = t.direct_members[name]
                if not isinstance(m, FieldIndex):
                    return m
            except KeyError:
                continue
        raise KeyError(f"{self} has no member '{name}'!")


def as_atomic(instance, atomic):
    """
    Maps a Value object the type of which is a subclass of an atomic type to a Value object the type of which is
    equal to that atomic type.
    :param instance: A Value object.
    :param atomic: Either an AtomicType that 'instance' is an instance of, or a tuple
    :return: A Value object the type of which is identical to 'atomic'.
    """

    if isinstance(atomic, AtomicType):
        atomic = [atomic]

    if isinstance(instance.type, AtomicType) and any(instance.type.subtypeof(a) for a in atomic):
        return instance
    elif isinstance(instance, VCompound):
        assert isinstance(instance.type, CompoundType)
        return instance[instance.type.get_atomic_base_field(atomic)]
    else:
        raise TypeError(f"The given instance is neither a VCompound object, nor an instance of an AtomicType!")


class VCompound(Value):
    """
    An instance of a compound type.
    """

    def __init__(self, t):
        """
        Creates a compound value.
        :param t: The CompoundType that the new object is to be an instance of.
        """
        super().__init__()
        self._type = check_type(t, CompoundType)
        self._fields = [value_none, ] * t.size

    @property
    def type(self):
        """
        The type that this value belongs to.
        :return: A Type object.
        """
        return self._type

    def hash(self):
        return len(self._fields)

    def _seal(self):
        for f in self._fields:
            f.seal()

    def print(self, out):
        out.write("Compound(")
        self.type.print(out)
        out.write(f", {id(self)})")

    def equals(self, other):
        return self is other

    def bequals(self, other, bijection):
        try:
            return bijection[id(self)] == id(other)
        except KeyError:
            bijection[id(self)] = id(other)
            if not (isinstance(other, VCompound)
                    and self._type.bequals(other._type, bijection)):
                return False
            return all(a.bequals(b, bijection) for a, b in zip(self._fields, other._fields))

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
            c = VCompound(self._type)
            clones[id(self)] = c
            c._type = c._type.clone_unsealed(clones=clones)
            c._fields = [f.clone_unsealed(clones=clones) for f in self._fields]
            return c

    def __getitem__(self, item):
        return self._fields[int(item)]

    def __setitem__(self, key, value):
        check_unsealed(self)
        self._fields[int(key)] = check_type(value, Value)
