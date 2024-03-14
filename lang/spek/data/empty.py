from engine.core.procedure import Procedure
from engine.core.singleton import SingletonValue


class EmptyProcedure(SingletonValue, Procedure):
    """
    A procedure that does nothing.
    """

    def initiate(self, tstate, mstate, *args):
        pass

    def print(self, out):
        return "<empty procedure>"