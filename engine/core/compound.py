from abc import ABC

from engine.core.atomic import type_type, AtomicType
from engine.core.none import VNone
from engine.core.type import Type
from engine.core.value import Value
from util import check_type
from util.immutable import check_unsealed


class CompoundType(Type, ABC):
    """
    A type the instances of which consist of tuples of other type instances.
    """

    def __init__(self, name, bases, num_direct_fields, direct_members):
        """
        Creates a new type.
        :param name: The name of this type.
        :param bases: A tuple of Type objects that the new type inherits from.
        :param direct_members: A mapping from names to Values that defines the *direct* members of this type.
        :param num_direct_fields: The number of data fields in the instances of this type that are not inherited from the
                           super types.
        """
        super().__init__(name, bases, direct_members)
        self._num_direct_fields = num_direct_fields
        self._offsets = {}
        offset = 0
        for t in self._mro:
            self._offsets[t] = offset
            if isinstance(t, AtomicType):
                offset += 1
            elif isinstance(t, CompoundType):
                offset += t._num_direct_fields
            else:
                raise TypeError(f"Compound types can only inherit from atomic types and other compound types, not from {type(t)}!")
        self._size = offset

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
        Computes the offset at which the fields of the given super type begin in the instances of this type.
        :param t: A super type of this type. May even be this type itself.
        :return: An int.
        """
        return self._offsets[t]

    def new(self, *_):
        return VCompound(self, self.size)


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
        self._fields = (VNone.instance, ) * t.size

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

    def clone_unsealed(self, clones=None):
        if clones is None:
            clones = {}
        try:
            return clones[id(self)]
        except KeyError:
            c = VCompound(self._type)
            clones[id(self)] = c
            c._type = c._type.clone_unsealed(clones=clones)
            c._fields = tuple(f.clone_unsealed(clones=clones) for f in self._fields)
            return c

    def __getitem__(self, item):
        return self._fields[check_type(item, int)]

    def __setitem__(self, key, value):
        check_unsealed(self)
        self._fields[check_type(key, int)] = check_type(value, Value)
