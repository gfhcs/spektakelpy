import abc
from inspect import signature, Parameter

from engine.functional import Value


class IntrinsicException(Exception):
    """
    Raised when the execution of an intrinsic procedure fails.
    """
    pass


class IntrinsicProcedure(Value):
    """
    Represents a procedure the execution of which is opaque to the state machine, but that can manipulate the entire
    state of the machine.
    """

    @property
    @abc.abstractmethod
    def num_args(self):
        """
        The number of arguments required by this procedure.
        """
        pass

    @property
    def type(self):
        from engine.functional.types import TBuiltin
        return TBuiltin.procedure

    def _seal(self):
        pass

    def clone_unsealed(self, clones=None):
        return self

    @abc.abstractmethod
    def execute(self, tstate, mstate, *args):
        """
        Executes this intrinsic procedure on the given state, leading to a new state.
        This procedure may modify the given TaskState and MachineState objects.
        :param tstate: The unsealed TaskState object that this instruction is to be executed in.
        It must be part of the given machine state.
        Any references to task-local variables will be interpreted with respect to this task state.
        :param mstate: The unsealed MachineState object that this instruction is to be executed in.
        It must contain the given task state.
        :param args: The argument Values that this intrinsic procedure is being called for.
        :return: The return value of the intrinsic procedure.
        :raises: Any exceptions.
        """
        pass


class IntrinsicInstanceMethod(IntrinsicProcedure):
    """
    An instance method of a Python class that can also be used as an intrinsic procedure at runtime.
    """

    def __init__(self, m):
        super().__init__()
        self._m = m
        self.__isabstractmethod__ = getattr(m, '__isabstractmethod__', False)

    @property
    def num_args(self):
        return len(signature(self._m).parameters)

    def print(self, out):
        out.write("IntrinsicInstanceMethod(")
        out.write(str(self._m))
        out.write(")")

    def execute(self, tstate, mstate, instance, *args):
        return self._m(instance, *args)

    def hash(self):
        return hash(self._m)

    def equals(self, other):
        return isinstance(other, IntrinsicInstanceMethod) and self._m is other._m

    def bequals(self, other, bijection):
        return self.equals(other)

    def cequals(self, other):
        return self.equals(other)

    def __call__(self, instance, *args):
        return self._m(instance, *args)


class IntrinsicConstructor(IntrinsicProcedure):
    """
    An __init__ method of a Python class that can be used to create instances at runtime.
    """

    def __init__(self, c):
        """
        Wraps a Python procedure as a Spek constructor.
        :param c: The Python instance method that should be used as a Spek constructor. This is often a class's
                  __init__ method.
        """
        super().__init__()
        self._c = c
        s = signature(c)
        self._num_args = sum(1 for n, p in s.parameters.items() if n != "self" and p.kind == Parameter.POSITIONAL_OR_KEYWORD)

    @property
    def num_args(self):
        return self._num_args

    def print(self, out):
        out.write("IntrinsicConstructor(")
        out.write(str(self._c))
        out.write(")")

    def execute(self, _, __, *args):
        return self._c(*args)

    def hash(self):
        return hash(self._c)

    def equals(self, other):
        return isinstance(other, IntrinsicConstructor) and self._c is other._c

    def bequals(self, other, bijection):
        return self.equals(other)

    def cequals(self, other):
        return self.equals(other)
