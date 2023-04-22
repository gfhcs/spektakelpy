import abc

from util import check_type
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

    def __init__(self, *children):
        super().__init__()
        for c in children:
            check_type(c, Term)
        self._children = children

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

    @property
    def children(self):
        """
        The children of this term.
        """
        return self._children

class CInt(Term):
    pass

class CFloat(Term):
    pass

class CTrue(Term):
    pass

class CFalse(Term):
    pass

class CNone(Term):
    pass

class CString(Term):
    pass


class Read(Term):
    pass

class Project(Term):
    pass


class StoreAttrCase(Term):
    # TODO: Für AttrCase sollten wir den Kommentar im Translation-Code als Dokumentation nutzen.
    pass

class LoadAttrCase(Term):
    # TODO: Für AttrCase sollten wir den Kommentar im Translation-Code als Dokumentation nutzen.
    pass

class IsTerminated(Term):
    pass

class IsCallable(Term):
    pass

class IsException(Term):
    pass


class Adjunction(Term):
    # TODO: This should call engine.tasks.dynamic.Namespace.adjoin
    pass

class Lookup(Term):
    # TODO: This should call engine.tasks.dynamic.Namespace.lookup
    pass

class Tuple(Term):
    pass


class UnaryOperation(Term):
    pass

class ArithmeticBinaryOperation(Term):
    pass

class BooleanBinaryOperation(Term):
    pass

class CTypeError(Term):
    pass

class NumArgs(Term):
    pass

class Comparison(Term):
    pass

class NewModule(Term):
    pass

class NewNamespace(Term):
    pass

class NewDict(Term):
    pass

class Function(Term):
    pass

class NewClass(Term):
    pass

class NewProperty(Term):
    pass

class Is(Term):
    pass

class IsInstance(Term):
    pass

class Member(Term):
    pass

class ContinueException(Term):
    pass

class BreakException(Term):
    pass

class NewReturnException(Term):
    pass

