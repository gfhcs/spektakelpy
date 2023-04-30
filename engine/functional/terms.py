import abc
from abc import ABC
from enum import Enum

from util import check_type
from .types import TException, TFunction, Type
from .values import Value, VInt, VFloat, VBoolean, VNone, VTuple, VTypeError
from ..task import TaskStatus
from ..tasks.reference import Reference


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


class ArithmeticUnaryOperator(Enum):
    """
    A unary operator.
    """
    MINUS = 0
    NOT = 1


class ArithmeticUnaryOperation(Term):
    """
    A term with one operand term.
    """

    def __init__(self, op, arg):
        """
        Creates a new unary operation.
        :param op: The operator for this operation.
        :param arg: The operand term.
        """
        super().__init__(check_type(arg, Term))
        self._op = check_type(op, ArithmeticUnaryOperator)

    @property
    def operand(self):
        """
        The operand term.
        """
        return self.children[0]

    @property
    def operator(self):
        """
        The operator of this operation.
        """
        return self._op

    def evaluate(self, tstate, mstate):
        r = self.operand.evaluate(tstate, mstate)
        if self._op == ArithmeticUnaryOperator.NOT:
            return ~r
        elif self._op == ArithmeticUnaryOperator.MINUS:
            return -r
        else:
            raise NotImplementedError()


class BinaryTerm(Term, ABC):
    """
    A term with two operands.
    """

    def __init__(self, op, left, right):
        """
        Creates a new binary operation.
        :param op: The operator for this term.
        :param left: The left operand term.
        :param right: The right operand term.
        """
        super().__init__(check_type(left, Term), check_type(right, Term))
        self._op = check_type(op, Enum)

    @property
    def left(self):
        """
        The left operand term.
        """
        return self.children[0]

    @property
    def right(self):
        """
        The right operand term.
        """
        return self.children[1]

    @property
    def operator(self):
        """
        The operator of this operation.
        """
        return self._op


class ArithmeticBinaryOperator(Enum):
    """
    An binary arithmetic operator.
    """
    PLUS = 0
    MINUS = 1
    TIMES = 2
    OVER = 3
    MODULO = 4
    POWER = 5
    INTOVER = 6


class ArithmeticBinaryOperation(BinaryTerm):
    """
    A binary arithmetic operation.
    """

    def __init__(self, op, left, right):
        """
        Creates a new binary arithmetic operation.
        :param op: The binary arithmetic operator for this operation.
        :param left: See BinaryOperation constructor.
        :param right: See BinaryOperation constructor.
        """
        super().__init__(check_type(op, ArithmeticBinaryOperator), left, right)

    def evaluate(self, tstate, mstate):
        left = self.left.evaluate(tstate, mstate)
        right = self.right.evaluate(tstate, mstate)

        if self.operator == ArithmeticBinaryOperator.PLUS:
            return left + right
        elif self.operator == ArithmeticBinaryOperator.MINUS:
            return left - right
        elif self.operator == ArithmeticBinaryOperator.TIMES:
            return left * right
        elif self.operator == ArithmeticBinaryOperator.OVER:
            return left / right
        elif self.operator == ArithmeticBinaryOperator.INTOVER:
            return left // right
        elif self.operator == ArithmeticBinaryOperator.MODULO:
            return left % right
        elif self.operator == ArithmeticBinaryOperator.POWER:
            return left ** right
        else:
            raise NotImplementedError()


class BooleanBinaryOperator(Enum):
    """
    A binary boolean operator.
    """
    AND = 0
    OR = 1


class BooleanBinaryOperation(BinaryTerm):
    """
    A binary boolean operation.
    """
    def __init__(self, op, left, right):
        """
        Creates a new binary boolean operation.
        :param op: The binary boolean operator for this operation.
        :param left: See BinaryOperation constructor.
        :param right: See BinaryOperation constructor.
        """
        super().__init__(check_type(op, BooleanBinaryOperator), left, right)

    def evaluate(self, tstate, mstate):
        left = self.left.evaluate(tstate, mstate)

        if self.operator == BooleanBinaryOperator.AND:
            return left and self.right.evaluate(tstate, mstate)
        elif self.operator == BooleanBinaryOperator.OR:
            return left or self.right.evaluate(tstate, mstate)
        else:
            raise NotImplementedError()


class ComparisonOperator(Enum):
    """
    Specifies a type of comparison.
    """
    EQ = 0
    NEQ = 1
    LESS = 2
    LESSOREQUAL = 3
    GREATER = 4
    GREATEROREQUAL = 5
    IN = 6
    NOTIN = 7
    IS = 8
    ISNOT = 9


class Comparison(BinaryTerm):
    """
    A term comparing two values.
    """

    def __init__(self, op, left, right):
        """
        Creates a new comparison term.
        :param op: The comparison operator for this comparison.
        :param left: The left hand side of the comparison.
        :param right: The right hand side of the comparison.
        """
        super().__init__(check_type(op, ComparisonOperator), left, right)

    def evaluate(self, tstate, mstate):
        left = self.left.evaluate(tstate, mstate)
        right = self.right.evaluate(tstate, mstate)

        if self.operator == ComparisonOperator.EQ:
            return left == right
        elif self.operator == ComparisonOperator.NEQ:
            return left != right
        elif self.operator == ComparisonOperator.LESS:
            return left < right
        elif self.operator == ComparisonOperator.LESSOREQUAL:
            return left <= right
        elif self.operator == ComparisonOperator.GREATER:
            return left > right
        elif self.operator == ComparisonOperator.GREATEROREQUAL:
            return left >= right
        elif self.operator == ComparisonOperator.IN:
            return left in right
        elif self.operator == ComparisonOperator.NOTIN:
            return left not in right
        elif self.operator == ComparisonOperator.IS:
            assert isinstance(left, Reference)
            assert isinstance(right, Reference)
            return left is right
        elif self.operator == ComparisonOperator.ISNOT:
            assert isinstance(left, Reference)
            assert isinstance(right, Reference)
            return left is not right
        else:
            raise NotImplementedError()


class UnaryPredicate(Enum):
    """
    A predicate that takes one argument.
    """
    ISCALLABLE = 0
    ISEXCEPTION = 1
    ISTERMINATED = 2


class UnaryPredicateTerm(Term):
    """
    A predicate evaluation.
    """

    def __init__(self, p, arg):
        """
        Creates a new unary predicate term.
        :param p: The UnaryPredicate for this operation.
        :param arg: The operand term.
        """
        super().__init__(check_type(arg, Term))
        self._p = check_type(p, UnaryPredicate)

    @property
    def operand(self):
        """
        The operand term.
        """
        return self.children[0]

    @property
    def predicate(self):
        """
        The predicate this term is querying.
        """
        return self._p

    def evaluate(self, tstate, mstate):
        r = self.operand.evaluate(tstate, mstate)
        t = r.type
        if self._p == UnaryPredicate.ISCALLABLE:
            # Check if it is a function object, a class object, or if the type of the object has a __call__ method.
            try:
                value = t.subtypeof(TFunction.instance) or t.subtypeof(Type.instance) \
                        or t.resolve_member("__call__", r).subtypeof(TFunction.instance)
            except KeyError:
                value = False
        elif self._p == UnaryPredicate.ISEXCEPTION:
            # Check if the type of the object is a descendant of TException:
            value = t.subtypeof(TException.instance)
        elif self._p == UnaryPredicate.ISTERMINATED:
            # Check if the argument TID refers to a terminated task.
            value = mstate.get_task_state(r.value).status in (TaskStatus.COMPLETED, TaskStatus.FAILED)
        else:
            raise NotImplementedError()

        return VBoolean(value)


class IsInstance(Term):
    """
    A term deciding if an object is an instance of a given type.
    """

    def __init__(self, value, types):
        """
        Creates a new IsInstance term.
        :param value: The term the type of which is to be inspected.
        :param types: A term evaluating to either a single type or a tuple of types.
        """
        super().__init__(check_type(value, Term), check_type(types, Term))

    @property
    def value(self):
        """
        The term the type of which is to be inspected.
        """
        return self.children[0]

    @property
    def types(self):
        """
        A term evaluating to either a single type or a tuple of types.
        """
        return self.children[1]

    def evaluate(self, tstate, mstate):
        v = self.value.evaluate(tstate, mstate)
        t = self.types.evaluate(tstate, mstate)

        if isinstance(t, Type):
            return CBool(v.type.subtypeof(t))
        elif isinstance(t, VTuple):
            for tt in t:
                if not isinstance(tt, Type):
                    raise VTypeError("isinstance(() arg 2 must be a type or tuple of types.")
                if v.type.subtypeof(tt):
                    return CBool(True)
            return CBool(False)
        else:
            raise TypeError()


class Read(Term):
    """
    A term that resolves a Reference value.
    """

    def __init__(self, r):
        """
        Creates a new Read term.
        :param r: A term specifying the reference to be read.
        """
        super().__init__(r)

    @property
    def reference(self):
        return self.children[0]

    def evaluate(self, tstate, mstate):
        r = self.reference
        assert isinstance(r, Reference)
        return r.read(tstate, mstate)


class Project(Term):
    """
    A term projecting a tuple to one of its components.
    """

    def __init__(self, tuple, index):
        """
        Creates a new projection term.
        :param tuple: A term evaluating to a tuple.
        :param index: A term evaluating to an integer.
        """
        super().__init__(check_type(tuple, Term), check_type(index, Term))

    @property
    def tuple(self):
        """
        A term evaluating to the tuple that is to be projected.
        """
        return self.children[0]

    @property
    def index(self):
        """
        A term evaluating to the index to which the tuple is to be projected.
        """
        return self.children[1]

    def evaluate(self, tstate, mstate):
        t = self.tuple.evaluate(tstate, mstate)
        i = self.index.evaluate(tstate, mstate)
        return t[i]


class Lookup(Term):
    """
    A term that queries a namespace.
    """
    def __init__(self, namespace, name):
        """
        Creates a new namespace lookup.
        :param namespace: A term evaluating to a Namespace value.
        :param name: A string specifying the name that is to be looked up.
        """
        super().__init__(check_type(namespace, Term))
        self._name = check_type(name, str)

    @property
    def namespace(self):
        """
        A term evaluating to name space that is to be queried.
        """
        return self.children[0]

    @property
    def name(self):
        """
        A string specifying the name that is to be looked up.
        """
        return self._name

    def evaluate(self, tstate, mstate):
        return self.namespace.evaluate(tstate, mstate).lookup(self.name)


class LoadAttrCase(Term):
    # TODO: Für AttrCase sollten wir den Kommentar im Translation-Code als Dokumentation nutzen.
    # TODO: Alle Referenzen auf Terme des Typs 'Member' müssen durch LoadAttrCase ersetzt werden!
    pass

class StoreAttrCase(Term):
    # TODO: Für AttrCase sollten wir den Kommentar im Translation-Code als Dokumentation nutzen.
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

