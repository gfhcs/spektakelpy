from inspect import signature, Parameter

from engine.core.type import Type
from util import check_types, check_type
from util.immutable import Immutable


class AtomicType(Type, Immutable):
    """
    A type the instances of which are opaque and indivisible.
    """

    def __init__(self, name, bases, new=None, members=None):
        """
        Creates a new atomic type.
        :param name: The name of the new type.
        :param bases: The base types the new type is supposed to inherit from.
        :param new: A procedure that takes constructor arguments and constructs an uninitialized instance of this type.
                    If None is given, the type will not have a visible constructor.
        :param members: The direct members of this type.
        """
        super().__init__(name, check_types(bases, Immutable), {} if members is None else {n: check_type(m, Immutable) for n, m in members.items()})
        super(Type, self).__init__()
        self._new = new

    def num_cargs(self):
        if self._new is None:
            raise RuntimeError(f"The type {self.name} does not have a public constructor!")
        return sum(1 for p in signature(self._new).parameters.values() if p.kind == Parameter.POSITIONAL_OR_KEYWORD)

    def new(self, *args):
        if self._new is None:
            raise RuntimeError(f"The type {self.name} does not have a public constructor!")
        return self._new(*args)

    @property
    def type(self):
        return type_type


type_object = AtomicType("object", [])
type_type = AtomicType("type", [type_object])
