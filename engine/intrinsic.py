import abc

from engine.functional.values import Value


class IntrinsicProcedure(Value):
    """
    Represents a procedure the execution of which is opaque to the state machine, but that can manipulate the entire
    state of the machine.
    """

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
        """
        pass


class IntrinsicInstanceMethod(IntrinsicProcedure):
    """
    An instance method of a Python class that can also be used as an intrinsic procedure at runtime.
    """

    def __init__(self, m):
        super().__init__()
        self._m = m

    def execute(self, tstate, mstate, instance, *args):
        try:
            tstate.returned = self._m(instance, *args)
        except Exception as ex:
            tstate.exception = IntrinsicException(ex)

    def hash(self):
        return hash(self._m)

    def equals(self, other):
        return isinstance(other, IntrinsicInstanceMethod) and self._m is other._m

    def __call__(self, instance, *args):
        return self._m(instance, *args)
