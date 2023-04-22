import abc

from util import check_type
from .values import Value, VInt, VFloat, VBoolean, VNone


class Term(abc.ABC):
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


class CTerm(Term):
    """
    A term that represents a constant value.
    """

    def __init__(self, value):
        """
        Instantiates a new constant term.
        :param value: The Value object that this term should evaluate to.
        """
        super().__init__()
        self._value = check_type(value, Value)

    def evaluate(self, tstate, mstate):
        return self._value


class CInt(CTerm):
    """
    A term that represents an integer constant.
    """

    def __init__(self, value):
        """
        Instantiates a new integer constant term.
        :param value: The integer this term is supposed to represent.
        """
        super().__init__(VInt(value))


class CFloat(CTerm):
    """
    A term that represents an float constant.
    """

    def __init__(self, value):
        """
        Instantiates a new float constant term.
        :param value: The float this term is supposed to represent.
        """
        super().__init__(VFloat(value))


class CBool(CTerm):
    """
    A term that represents a boolean constant.
    """

    def __init__(self, value):
        """
        Instantiates a new boolean constant term.
        :param value: The boolean this term is supposed to represent.
        """
        super().__init__(VBoolean(value))


class CNone(CTerm):
    """
    A term that represents the None constant.
    """

    def __init__(self):
        """
        Instantiates a new None term.
        """
        super().__init__(VNone.instance)


class UnaryOperation(Term):
    pass

class ArithmeticBinaryOperation(Term):
    pass

class BooleanBinaryOperation(Term):
    pass

class Comparison(Term):
    pass

class Is(Term):
    pass

class IsInstance(Term):
    pass

class IsCallable(Term):
    pass

class IsException(Term):
    pass

class IsTerminated(Term):
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

class Member(Term):
    pass

class Lookup(Term):
    # TODO: This should call engine.tasks.dynamic.Namespace.lookup
    pass

class Adjunction(Term):
    # TODO: This should call engine.tasks.dynamic.Namespace.adjoin
    pass

class NewString(Term):
    pass

class NewTuple(Term):
    pass

class NewDict(Term):
    pass

class NewTypeError(Term):
    pass

class NewReturnException(Term):
    pass

class NewContinueException(Term):
    pass

class NewBreakException(Term):
    pass

class NewFunction(Term):
    pass

class NumArgs(Term):
    pass

class NewProperty(Term):
    pass

class NewNamespace(Term):
    pass

class NewModule(Term):
    pass

class NewClass(Term):
    pass



