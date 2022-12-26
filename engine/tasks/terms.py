import abc
from util.immutable import Immutable


class EvaluationException(Exception):
    # TODO: This must be a value!
    pass


class Term(Immutable, abc.ABC):
    """
    Defines the types and semantics of expressions that the virtual machine can evaluate.
    A term is an expression the evaluation of which happens atomically and cannot cause any side effects.
    This means that evaluation is not observable and that evaluating a term can in no way change the machine state.
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


class CTrue(Term):
    pass

class CFalse(Term):
    pass

class CNone(Term):
    pass

class Adjunction(Term):
    # TODO: This should call engine.tasks.dynamic.Namespace.adjoin
    pass

class Lookup(Term):
    # TODO: This should call engine.tasks.dynamic.Namespace.lookup
    pass


# TODO: I want an expression that tells me an upper bound of the heap length.
#       This can be used for allocating new memory.

# TODO: Expression must not have side effects and must be executed atomically! This means that there cannot be expressions for Calls, Launches or Awaits!
