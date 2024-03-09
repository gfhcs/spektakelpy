from engine.core.procedure import Procedure
from engine.core.property import Property
from util import check_type


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
    def getter_procedure(self):
        return self._getter

    @property
    def setter_procedure(self):
        return self._setter

    def print(self, out):
        out.write("OrdinaryProperty(")
        self.getter_procedure.print(out)
        if self.setter_procedure is not None:
            out.write(", ")
            self.setter_procedure.print(out)
        out.write(")")

    def hash(self):
        return id(self)

    def equals(self, other):
        return self is other

    def bequals(self, other, bijection):
        return self is other

    def cequals(self, other):
        return self is other

    def clone_unsealed(self, clones=None):
        return self

    def _seal(self):
        self._getter.seal()
        self._setter.seal()
