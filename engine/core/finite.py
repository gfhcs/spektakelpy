
from abc import ABC

from engine.core.value import Value
from util.finite import Finite


class FiniteValue(Finite, Value, ABC):
    """
    A Value subtype that is also a subtype of Finite.
    """

    def bequals(self, other, _):
        return self is other

    def cequals(self, other):
        return self is other

    def chash(self):
        return self.instance_index