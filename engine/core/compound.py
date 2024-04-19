from abc import ABC

from engine.core.atomic import type_type, AtomicType
from engine.core.finite import FiniteValue
from engine.core.none import value_none
from engine.core.type import Type
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

        dummy = AtomicType("", bases)
        offsets = {}
        offset = 0
        for t in dummy.mro:
            offsets[id(t)] = offset
            if t is dummy:
                for n in direct_field_names:
                    direct_members[n] = FieldIndex(offset)
                    offset += 1
            elif isinstance(t, AtomicType):
                offset += 1
            elif isinstance(t, CompoundType):
                for n, member in t.direct_members:
                    if isinstance(member, FieldIndex):
                        direct_members[n] = FieldIndex(offset)
                        offset += 1
            else:
                raise TypeError(f"Compound types can only inherit from atomic types and other compound types, not from {type(t)}!")
        super().__init__(name, bases, direct_members)
        self._size = offset
        offsets[id(self)] = offsets[id(dummy)]
        del offsets[id(dummy)]
        self._offsets = offsets

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
        return self._offsets[id(t)]

    def new(self, *_):
        return VCompound(self)


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
        return self._fields[check_type(item, int)]

    def __setitem__(self, key, value):
        check_unsealed(self)
        self._fields[check_type(key, int)] = check_type(value, Value)
