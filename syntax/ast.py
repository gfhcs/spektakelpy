import abc
from enum import Enum

from util import check_type
from .lexer import TokenPosition
from .state import Value


class Node:
    """
    A node in an abstract syntax tree.
    """

    def __init__(self, *children, start=None, end=None):
        super().__init__()

        for c in children:
            check_type(c, Node)

        self._children = children
        self._start = check_type(start, TokenPosition)
        self._end = check_type(end, TokenPosition)

    @property
    def start(self):
        """
        The position inside a source stream, from which this node was parsed.
        :return: A TokenPosition object, or None, if this node was not parsed from an input stream.
        """
        return self._start

    @property
    def end(self):
        """
        The position inside a source stream, up to which this node was parsed.
        :return: A TokenPosition object, or None, if this node was not parsed from an input stream.
        """
        return self._end

    @property
    def children(self):
        """
        The children of this node.
        """
        return self._children


class Expression(Node, abc.ABC):
    """
    A syntactic object that can be evaluated to obtain a value.
    """
    def __init__(self, *largs, **kwargs):
        super().__init__(*largs, **kwargs)
        self._vars = None

    def variables(self):
        """
        An iterable of the variables occuring in this expression.
        :return: An iterable without duplicates.
        """
        if self._vars is None:
            self._vars = frozenset(v for c in self.children for v in c.variables)

        return self._vars


class Constant(Expression):
    """
    An expression that does not have any children and always evaluates to the same value, regardless of the given
    valuation.
    """
    def __init__(self, value, start=None, end=None):
        super().__init__(start=start, end=end)
        self._value = check_type(value, Value)

    @property
    def value(self):
        """
        The Value object that this constant represents.
        """
        return self._value


class AssignableExpression(Expression, abc.ABC):
    """
    An expression that may represent the target of a write operation.
    """

    def __init__(self, *largs, assigned=False, **kwargs):
        """
        Creates a new potentially assignable expression.
        :param largs: See Expression constructor.
        :param assigned: Whether this expression is the target of an assignment.
        :param kwargs: See Expression constructor.
        """
        super().__init__(*largs, **kwargs)
        self._assigned = check_type(assigned, bool)

    @property
    def assigned(self):
        """
        Indicates if this expression is (part of) the target of an assignment.
        """
        return self._assigned


class Identifier(AssignableExpression):
    """
    An identifier.
    """

    def __init__(self, name, **kwargs):
        """
        Creates a new identifier expression
        :param name: The name of this identifier.
        :param kwargs: See AssignableExpression constructor.
        """
        super().__init__(**kwargs)
        self._name = check_type(name, str)

    @property
    def name(self):
        """
        The name of this identifier.
        """
        return self._name


class Tuple(AssignableExpression):
    """
    A tuple expression.
    """
    def __init__(self, *components, **kwargs):
        """
        Creates a new tuple expression.
        :param components: The expressions for the tuple components.
        :param kwargs: See AssigneableExpression constructor.
        """
        super().__init__(*(check_type(c, Expression) for c in components), **kwargs)


class Projection(AssignableExpression):
    """
    An expression representing a particular component of a sequence.
    """
    def __init__(self, target, index, **kwargs):
        """
        Creates a new projection expression.
        :param components: The expression representing the sequence to project from.
        :param index: The expression representing the projection index.
        :param kwargs: See AssigneableExpression constructor.
        """
        super().__init__(check_type(target, Expression), check_type(index, Expression), **kwargs)


class Attribute(AssignableExpression):
    """
    An expression representing an attribute of a value.
    """
    def __init__(self, value, identifier, **kwargs):
        """
        Creates an attribute lookup.
        :param value: The expression representing the value to retrieve the attribute form.
        :param identifier: The identifier of the attribute to retrieve.
        :param kwargs: See AssigneableExpression constructor.
        """
        super().__init__(check_type(value, Expression), **kwargs)
        self._identifier = check_type(identifier, str)

    @property
    def name(self):
        """
        The name of this attribute.
        """
        return self._identifier


class Call(Expression):
    """
    A call to a procedure.
    """
    def __init__(self, identifier, *args, **kwargs):
        """
        Creates procedure call.
        :param identifier: The expression representing the procedure to be called.
        :param args: The expressions representing the arguments to the call.
        :param kwargs: See AssigneableExpression constructor.
        """
        super().__init__(check_type(identifier, str), *(check_type(a, Expression) for a in args), **kwargs)

    @property
    def identifier(self):
        """
        The name of the procedure that is called.
        """
        return self.children[0]

    def arguments(self):
        """
        The expressions representing the arguments to the call.
        """
        return self.children[1:]


class UnaryOperator(Enum):
    """
    A unary operator.
    """
    MINUS = 0
    NOT = 0


class UnaryOperation(Expression, abc.ABC):
    """
    An operation with one operand.
    """

    def __init__(self, op, arg, **kwargs):
        """
        Creates a new unary operation.
        :param op: The operator for this operation.
        :param left: The operand expression.
        :param kwargs: See Expression constructor.
        """
        super().__init__(check_type(arg, Expression), **kwargs)
        self._op = check_type(op, Enum)

    @property
    def operand(self):
        """
        The operand expression.
        """
        return self.children[0]

    @property
    def operator(self):
        """
        The operator of this operation.
        """
        return self._op


class BinaryOperation(Expression):
    """
    An operation with two operands.
    """

    def __init__(self, op, left, right, **kwargs):
        """
        Creates a new binary operation.
        :param op: The operator for this operation.
        :param left: The left operand expression.
        :param right: The right operand expression.
        :param kwargs: See Expression constructor.
        """
        super().__init__(check_type(left, Expression), check_type(right, Expression), **kwargs)
        self._op = check_type(op, Enum)

    @property
    def left(self):
        """
        The left operand expression.
        """
        return self.children[0]

    @property
    def right(self):
        """
        The right operand expression.
        """
        return self.children[1]

    @property
    def operator(self):
        """
        The operator of this operation.
        """
        return self._op


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


class Comparison(BinaryOperation):
    """
    An expression comparing two values.
    """

    def __init__(self, op, left, right, **kwargs):
        """
        Creates a new comparison expression.
        :param op: The comparison operator for this comparison.
        :param left: The left hand side of the comparison.
        :param right: The right hand side of the comparison.
        :param kwargs: See Expression constructor.
        """
        super().__init__(check_type(op, ComparisonOperator), left, right, **kwargs)


class BooleanBinaryOperator(Enum):
    """
    A binary boolean operator.
    """
    AND = 0
    OR = 1


class BooleanBinaryOperation(BinaryOperation):
    """
    A binary boolean operation.
    """
    def __init__(self, op, left, right, **kwargs):
        """
        Creates a new binary boolean operation.
        :param op: The binary boolean operator for this operation.
        :param left: See BinaryOperation constructor.
        :param right: See BinaryOperation constructor.
        :param kwargs: See BinaryOperation constructor.
        """
        super().__init__(check_type(op, BooleanBinaryOperator), left, right, **kwargs)


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


class ArithmeticBinaryOperation(BinaryOperation):
    """
    A binary arithmetic operation.
    """
    def __init__(self, op, left, right, **kwargs):
        """
        Creates a new binary arithmetic operation.
        :param op: The binary arithmetic operator for this operation.
        :param left: See BinaryOperation constructor.
        :param right: See BinaryOperation constructor.
        :param kwargs: See BinaryOperation constructor.
        """
        super().__init__(check_type(op, ArithmeticBinaryOperator), left, right, **kwargs)

