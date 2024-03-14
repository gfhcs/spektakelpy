
from abc import ABC

from engine.core.value import Value
from util.keyable import Keyable


class KeyableValue(Keyable, Value, ABC):
    """
    A Value subtype that is also a subtype of Keyable.
    """

    def bequals(self, other, _):
        return self is other

    def cequals(self, other):
        return self is other
