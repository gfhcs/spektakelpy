from engine.core.atomic import EmptyMember, type_object
from engine.core.compound import CompoundType, FieldIndex
from engine.core.intrinsic import intrinsic_type
from engine.core.type import Type
from engine.core.value import Value
from engine.stack.exceptions import VTypeError
from engine.stack.procedure import StackProcedure
from lang.spek.data.bound import BoundProcedure
from lang.spek.data.builtin import builtin
from util import check_type


class Class(CompoundType):
    """
    Represents a user-defined class.
    """

    def __init__(self, name, bases, direct_field_names, direct_members):
        """
        Creates a new class.
        :param name: The name of the class.
        :param bases: The Types this class is inheriting from.
        :param direct_field_names: The names of the direct fields of instances of this class.
        :param direct_members: A dict mapping member names to the direct (i.e. not inherited) members of this class.
        """
        super().__init__(name, bases, direct_field_names, direct_members)
        self._direct_field_names = direct_field_names

    @property
    def num_cargs(self):
        try:
            initializer = self.resolve_member("__init__")
        except KeyError:
            return 0

        num_args = -1 # 'self' is not a constructor argument.
        while True:
            if isinstance(initializer, StackProcedure):
                num_args += initializer.num_args
                break
            elif isinstance(initializer, EmptyMember):
                # This represents the empty initializer, that takes only 'self' as argument:
                num_args += 1
                break
            elif isinstance(initializer, BoundProcedure):
                num_args -= sum(1 for v in initializer.bound if v is not None)
                initializer = initializer.core
            else:
                raise VTypeError(f"The number of constructor arguments for the class {self.name} cannot be determined!")

        assert num_args >= 0

        return num_args

    def clone_unsealed(self, clones=None):
        if clones is None:
            clones = {}
        try:
            return clones[id(self)]
        except KeyError:
            c = Class(self.name, self.bases, self._direct_field_names, self.direct_members)
            clones[id(self)] = c
            c._update_clone(tuple(b.clone_unsealed(clones) for b in self.bases), {n: m.clone_unsealed(clones) for n, m in self.direct_members.items()})
            return c


@builtin()
@intrinsic_type("super", [type_object])
class VSuper(Value):
    """
    Equivalent to Python's 'super' type.
    """

    def __new__(cls, t, x):
        """
        Makes attribute resolution available for the given type and instance.
        :param t: The type up *after* which the MRO of the instance should be searched for attributes.
        :param x: The instance the MRO of which is to be searched for attributes.
        """

        if not x.type.subtypeof(t):
            raise VTypeError(f"The given instance is of type {x.type}, that is not a subtype of {t}!")

        instance = super().__new__(cls)
        instance._t = check_type(t, Type)
        instance._x = check_type(x, Value)

        return instance

    @property
    def instance(self):
        """
        The instance that was given to the constructor for this 'super' object.
        :return: A Value.
        """
        return self._x

    def print(self, out):
        out.write("super(")
        self._t.print(out)
        out.write(", ")
        self._x.print(out)
        out.write(")")

    @property
    def type(self):
        return VSuper.intrinsic_type

    def hash(self):
        return hash(self._x)

    def equals(self, other):
        return self is other

    def bequals(self, other, bijection):
        try:
            return bijection[id(self)] == id(other)
        except KeyError:
            bijection[id(self)] = id(other)
            return (isinstance(other, VSuper)
                    and self._t.bequals(other._t, bijection) and self._x.bequals(other._x, bijection))

    def cequals(self, other):
        return self is other

    def chash(self):
        return self._x.chash()

    def _seal(self):
        self._t.seal()
        self._x.seal()

    def clone_unsealed(self, clones=None):
        if clones is None:
            clones = {}
        try:
            return clones[id(self)]
        except KeyError:
            c = VSuper(self._t, self._x)
            clones[id(self)] = c
            c._t = self._t.clone_unsealed(clones=clones)
            c._x = self._x.clone_unsealed(clones=clones)
            return c

    def resolve_member(self, name, **kwargs):
        """
        Retrieves the member this super object assigns to the given name.
        :param name: A str object.
        :param kwargs: Command line arguments that will be ignored.
        :return: A Value object.
        :exception KeyError: If no member for the given name could be retrieved.
        """

        mro = iter(self._x.type.mro)

        while not next(mro).cequals(self._t):
            continue

        for t in mro:
            try:
                m = t.direct_members[name]
                if isinstance(m, FieldIndex):
                    continue
                return m
            except KeyError:
                continue
        raise KeyError(f"{self} has no member '{name}'!")
