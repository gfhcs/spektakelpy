from engine.core.atomic import AtomicType, type_object
from engine.core.value import Value
from util.immutable import Immutable


class VNone(Value, Immutable):
    """
    Equivalent of Python's 'None'.
    """

    @property
    def type(self):
        return type_none

    def hash(self):
        return 0

    def equals(self, other):
        return isinstance(other, VNone)

    def bequals(self, other, bijection):
        return self.equals(other)

    def cequals(self, other):
        return self.equals(other)

    def clone_unsealed(self, clones=None):
        return self

    def print(self, out):
        out.write("None")

    def __repr__(self):
        return "VNone.instance"


VNone.instance = VNone()


def new_none():
    return VNone.instance


type_none = AtomicType("none", [type_object], new=new_none)
