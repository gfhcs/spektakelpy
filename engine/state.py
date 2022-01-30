
from util import check_type
from .values import Value


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

    @property
    def name(self):
        """
        A descriptive name for this variable. It does not serve any semantic purpose.
        """
        return self._name


class Valuation:
    """
    A mapping of Variable objects to Value objects.
    """

    def __init__(self, m):
        """
        Creates a new valuation
        :param m: A dict mapping Variable objects to Value objects.
        """
        super().__init__()

        if isinstance(m, Valuation):
            self._m = dict(m._m)
        else:
            self._m = {check_type(k, Variable): check_type(v, Value) for k, v in m.items()}

    def __len__(self):
        return len(self._m)

    def __getitem__(self, var):
        return self._m[check_type(var, Variable)]

    def __setitem__(self, var, value):
        self._m[check_type(var, Variable)] = check_type(value, Value)

    def __iter__(self):
        return iter(self._m.items())

