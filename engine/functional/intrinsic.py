from engine.tasks.instructions import IntrinsicProcedure


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
