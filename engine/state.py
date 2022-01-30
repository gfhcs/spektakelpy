
from util import check_type
from util.immutable import ImmutableEquatable
from .values import Value
from util.environment import Environment


class Variable:
    """
    An object that values can be assigned to.
    """
    def __init__(self, name=None):
        """
        Creates a new variable.
        :param name: A descriptive name for this variable. It does not serve any semantic purpose.
        """
        super().__init__()
        self._name = name

    def __hash__(self):
        return hash(id(self))

    @property
    def name(self):
        """
        A descriptive name for this variable. It does not serve any semantic purpose.
        """
        return self._name


class Valuation(Environment, ImmutableEquatable):
    """
    A mapping of Variable objects to Value objects.
    """

    def __init__(self, m, base=None):
        """
        Creates a new valuation
        :param m: A dict mapping Variable objects to Value objects.
        :param base: A Valuation that serves as the basis for adjunction:
                     Any keys not mapped by m are defined by 'base'.
        """
        super().__init__(k2v={check_type(k, Variable): check_type(v, Value) for k, v in m.items()},
                         base=check_type(base, Valuation))
        self._hash = None

    def hash(self):
        if self._hash is None:
            h = len(self)
            for _, v in self:
                h ^= hash(v)
            self._hash = h

        return self._hash

    def equals(self, other):
        if not isinstance(other, Valuation) or other.hash() != self.hash():
            return False
        if len(self) != len(other):
            return False
        return all(other[var] == val for var, val in self)
