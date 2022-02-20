import abc
from util.immutable import Immutable


class EvaluationException(Exception):
    # TODO: This must be a value!
    pass


class Expression(Immutable, abc.ABC):
    """
    Models expressions and their semantics.
    """

    @abc.abstractmethod
    def evaluate(self, tstate, mstate):
        """
        Evaluates this expression in the given state.
        :param tstate: The task state that this expression is to be evaluated in. It must be part of the given machine
        state. Any references to task-local variables will be interpreted with respect to this task state.
        :param mstate: The machine state that this expression is to be evaluated in. It must contain the given task
        state.
        :exception EvaluationException: If evaluation fails for a semantic reason.
        :return: An object representing the value that evaluation resulted in.
        """
        pass


# TODO: I want an expression that tells me an upper bound of the heap length.
#       This can be used for allocating new memory.
