from engine.core.atomic import AtomicType, type_object
from engine.core.singleton import SingletonValue


class VNone(SingletonValue):
    """
    Equivalent of Python's 'None'.
    """

    @property
    def type(self):
        return type_none

    def print(self, out):
        out.write("None")

    def __repr__(self):
        return "value_none"


type_none = AtomicType("none", [type_object])
value_none = VNone()
