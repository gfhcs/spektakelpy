from util import check_type
from lang import OwnershipError
from model.behavior import SymbolicProcess
from legacy.core import CompactObject


class Variable(CompactObject):
    """
    A named objects that values can be assigned to.
    """
    def __init__(self, name, dtype):
        """
        Creates a new variable.
        :param name: The name by which this variable can be referred to syntactically.
        :param dtype: The type of the values assigned to this variable.
        """
        super().__init__()
        self._name = name
        self._dtype = dtype
        self._owner = None

    def hash(self):
        return id(self)

    def equal(self, other):
        return self is other

    def own(self, process):
        """
        Makes the given process the owner of this variable.
        :param process: The SymbolicProcess that owns this variable.
        """

        if self._owner is not None:
            raise OwnershipError("This variable is already owned by a process!")

        self._owner = check_type(process, SymbolicProcess)

    @property
    def name(self):
        """
        The name of this variable.
        """
        return self._name

    def dtype(self):
        """
        The type of the values assigned to this variable.
        :return: A subclass of Value.
        """
        return self._dtype


class Valuation(CompactObject):
    """
    A mapping of Variable objects to Value objects.
    """

    def __init__(self, m):
        """
        Creates a new valuation.
        :param m: A dict mapping Variable objects to Value objects.
        """
        super().__init__()
        self._m = {check_type(k, Variable): check_type(v, k.dtype) for k, v in m.items()}
        self._hash = None

    def __len__(self):
        return len(self._m)

    def __getitem__(self, var):
        return self._m[var]

    def __iter__(self):
        return iter(self._m.items())

    def equal(self, other):
        return isinstance(other, Valuation) \
               and len(self) == len(other) \
               and all(val == other[var] for var, val in self._m.items())

    def hash(self):
        if self._hash is None:
            self._hash = 0
            for val in self._m.values():
                self._hash ^= hash(val)
        return self._hash


