from abc import ABC
from inspect import signature, Parameter

from engine.core.singleton import SingletonValue
from engine.core.type import Type
from engine.core.value import Value
from util import check_types, check_type
from util.immutable import Immutable


class EmptyMember(SingletonValue):
    """
    A member that exists but has no intrinsic meaning.
    The only instance of this type is meant to be a placeholder.
    """

    @property
    def type(self):
        raise NotImplementedError("")

    def print(self, out):
        raise NotImplementedError("")


class AtomicType(Immutable, Type):
    """
    A type the instances of which are opaque and indivisible.
    """

    def __init__(self, name, bases, new=None, num_cargs=None, members=None):
        """
        Creates a new atomic type.
        :param name: The name of the new type.
        :param bases: An iterable of AtomicTypes that the new type is supposed to inherit from.
        :param new: A procedure that takes constructor arguments and constructs an uninitialized instance of this type.
                    If None is given, the type will not have a visible constructor.
        :param num_cargs: The number of arguments that the constructor for this type should accept.
        :param members: The direct members of this type.
        """
        super().__init__(name, check_types(bases, AtomicType), {} if members is None else {n: check_type(m, Immutable) for n, m in members.items()})
        self._new = new
        if num_cargs is None and new is not None:
            num_cargs = sum(1 for p in signature(self._new).parameters.values() if p.kind == Parameter.POSITIONAL_OR_KEYWORD)
        self._num_cargs = num_cargs

    @property
    def num_cargs(self):
        if self._new is None:
            raise RuntimeError(f"The type {self.name} does not have a public constructor!")
        return self._num_cargs

    def new(self, *args):
        if self._new is None:
            raise RuntimeError(f"The type {self.name} does not have a public constructor!")
        return self._new(*args)

    @property
    def type(self):
        return type_type


type_object = None


class VObject(Value):

    @property
    def type(self):
        global type_object
        return type_object

    def bequals(self, other, bijection):
        try:
            return bijection[id(self)] == id(other)
        except KeyError:
            bijection[id(self)] = id(other)
            return isinstance(other, VObject)

    def cequals(self, other):
        return self is other

    def chash(self):
        return 0

    def hash(self):
        return id(self)

    def equals(self, other):
        return self is other

    def _seal(self):
        pass

    def clone_unsealed(self, clones=None):
        if clones is None:
            clones = {}
        try:
            return clones[id(self)]
        except KeyError:
            c = VObject()
            clones[id(self)] = c
            return c

    def print(self, out):
        return super(ABC, self).__str__()


type_object = AtomicType("object", [], new=VObject, num_cargs=0, members={'__init__': EmptyMember()})
type_type = AtomicType("type", [type_object])
