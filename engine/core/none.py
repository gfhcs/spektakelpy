from engine.core.atomic import AtomicType, type_object
from engine.core.value import Value
from util.singleton import Singleton


class VNone(Value, Singleton):
    """
    Equivalent of Python's 'None'.
    """

    @property
    def type(self):
        return type_none

    def bequals(self, other, bijection):
        return self.equals(other)

    def cequals(self, other):
        return self.equals(other)

    def clone_unsealed(self, clones=None):
        return self

    def print(self, out):
        out.write("None")

    def __repr__(self):
        return "value_none"


type_none = AtomicType("none", [type_object])
value_none = VNone()
