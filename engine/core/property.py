import abc
from abc import ABC

from engine.core.atomic import type_object, AtomicType
from engine.core.procedure import Procedure
from engine.core.value import Value
from util import check_type


class Property(Value, ABC):
    """
    Represents an instance property.
    """

    intrinsic_type = AtomicType("property", [type_object])

    @property
    def type(self):
        return Property.intrinsic_type

    @property
    @abc.abstractmethod
    def getter(self):
        """
        The getter procedure for this property.
        """
        pass

    @property
    @abc.abstractmethod
    def setter(self):
        """
        Either None (in case of a readonly property), or the setter procedure for this property.
        """
        pass


class OrdinaryProperty(Property):
    """
    Represents a property defined by the user.
    """

    def __init__(self, getter, setter=None):
        """
        Creates a new user-defined property.
        :param getter: The getter procedure for this property.
        :param setter: Either None (in case of a readonly property), or the setter procedure for this property.
        """
        super().__init__()
        self._getter = check_type(getter, Procedure)
        self._setter = None if setter is None else check_type(setter, Procedure)

    @property
    def getter(self):
        return self._getter

    @property
    def setter(self):
        return self._setter

    def print(self, out):
        out.write("OrdinaryProperty(")
        self.getter.print(out)
        if self.setter is not None:
            out.write(", ")
            self.setter.print(out)
        out.write(")")

    def hash(self):
        return id(self)

    def equals(self, other):
        return self is other

    def bequals(self, other, bijection):
        try:
            return bijection[id(self)] == id(other)
        except KeyError:
            bijection[id(self)] = id(other)
            return (isinstance(other, OrdinaryProperty)
                    and self._getter.bequals(other._getter, bijection)
                    and (self._setter is None) == (other._setter is None)
                    and (self._setter is None or self._setter.bequals(other._setter, bijection)))

    def cequals(self, other):
        return self is other

    def chash(self):
        return hash((self._getter.chash(), (0 if self._setter is None else self._setter.chash())))

    def _seal(self):
        self._getter.seal()
        self._setter.seal()

    def clone_unsealed(self, clones=None):
        if clones is None:
            clones = {}
        try:
            return clones[id(self)]
        except KeyError:
            c = OrdinaryProperty(self._getter, self._setter)
            clones[id(self)] = c
            c._getter = self._getter.clone_unsealed(clones)
            c._setter = self._setter.clone_unsealed(clones)
            return c
