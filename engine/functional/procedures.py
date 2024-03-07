from inspect import signature

from engine.functional.values import VBool
from engine.intrinsic import IntrinsicProcedure


class PBuiltin(IntrinsicProcedure):
    """
    Represents a builtin procedure, i.e. one the user did neither define, nor explicitly import.
    """

    __instances = []

    def __init__(self, name, p):
        """
        Creates a new builtin procedure.
        :param name: The name under which this procedure will be visible globally.
        :param p: The procedure implementing self.execute, see IntrinsicProcedure.
        """

        super().__init__()
        self._name = name
        self._p = p
        self.seal()
        PBuiltin.__instances.append(self)

    @property
    def name(self):
        """
        The name under which this procedure should be visible globally.
        :return: A string.
        """
        return self._name

    @property
    def num_args(self):
        return len(signature(self._p).parameters) - 2

    def execute(self, tstate, mstate, *args):
        return self._p(tstate, mstate, *args)

    def print(self, out):
        out.write(f"<built-in {self._name}>")

    def hash(self):
        return hash(self._name)

    def equals(self, other):
        return isinstance(other, PBuiltin) and self._name == other._name and self._p is other._p

    def bequals(self, other, bijection):
        return self.equals(other)

    def cequals(self, other):
        return self.equals(other)

    def __call__(self, tstate, mstate, *args):
        return self._p(tstate, mstate, *args)

    @classmethod
    @property
    def instances(cls):
        """
        An iterable of all the instances of PBuiltin.
        """
        return iter(PBuiltin.__instances)


def builtin(name):
    """
    Registers a global procedure as a builtin procedure for spek.
    :param name: The builtin name under which to register the procedure.
    :return: A decorator procedure.
    """
    def decorate(p):
        PBuiltin(name, p)
    return decorate


@builtin("isinstance")
def builtin_isinstance(tstate, mstate, x, types):
    if not isinstance(types, tuple):
        types = (types, )
    t = x.type
    return VBool.from_bool(any(t.subtypeof(s) for s in types))
