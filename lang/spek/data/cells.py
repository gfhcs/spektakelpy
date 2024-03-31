from engine.core.atomic import type_object
from engine.core.intrinsic import intrinsic_type
from engine.core.value import Value
from engine.stack.exceptions import unhashable
from util import check_type
from util.immutable import check_unsealed


@intrinsic_type("cell", [type_object])
class VCell(Value):
    """
    An object that references another object.
    """

    def __init__(self, ref):

        """
        Creates a new cell.
        :param ref: The object this cell should contain.
        """
        super().__init__()
        self._ref = check_type(ref, Value)

    @property
    def value(self):
        """
        The object contained in this cell.
        :return: A Value.
        """
        return self._ref

    @value.setter
    def value(self, value):
        check_unsealed(self)
        self._ref = check_type(value, Value)

    def print(self, out):
        out.write("Cell(")
        self._ref.print(out)
        out.write(")")

    def __repr__(self):
        return f"VCell({repr(self._ref)})"

    @property
    def type(self):
        return VCell.intrinsic_type

    def hash(self):
        return hash(self._ref) ^ 47

    def equals(self, other):
        return self is other

    def bequals(self, other, bijection):
        try:
            return bijection[id(self)] == id(other)
        except KeyError:
            bijection[id(self)] = id(other)
            return isinstance(other, VCell) and self._ref.bequals(other._ref, bijection)

    def cequals(self, other):
        return self.equals(other)

    def chash(self):
        return unhashable(self)

    def _seal(self):
        self._ref.seal()

    def clone_unsealed(self, clones=None):
        if clones is None:
            clones = {}
        try:
            return clones[id(self)]
        except KeyError:
            c = VCell(self._ref)
            clones[id(self)] = c
            c._ref = self._ref.clone_unsealed(clones=clones)
            return c
