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
        self._identifier = check_type(identifier, Identifier)

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
    def __init__(self, callee, *args, **kwargs):
        """
        Creates procedure call.
        :param callee: The expression representing the procedure to be called.
        :param args: The expressions representing the arguments to the call.
        :param kwargs: See AssigneableExpression constructor.
        """
        super().__init__(check_type(callee, Expression), *(check_type(a, Expression) for a in args), **kwargs)

    @property
    def callee(self):
        """
        The procedure that is called.
        """
        return self.children[0]

    @property
    def arguments(self):
        """
        The expressions representing the arguments to the call.
        """
        return self.children[1:]


class Launch(Expression):
    """
    An expression launching a new process.
    """
    def __init__(self, call, **kwargs):
        """
        Creates a new process launch expression.
        :param call: A call expression representing the computation that
                     the newly launched process is supposed to execute.
        :param kwargs: See Expression constructor.
        """
        super().__init__(check_type(call, Call), **kwargs)

    @property
    def call(self):
        """
        The call that the new process is supposed to execute.
        :return: A Call object.
        """
        return self.children[0]


class Await(Expression):
    """
    An expression that evaluates to the return value of a process, after blocking until the process terminated.
    """
    def __init__(self, process, **kwargs):
        """
        Creates a new process launch expression.
        :param process: An expression representing the awaited process.
        :param kwargs: See Expression constructor.
        """
        super().__init__(check_type(process, Expression), **kwargs)

    @property
    def process(self):
        """
        An expression representing the awaited process.
        :return: An Expression object.
        """
        return self.children[0]


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


class Statement(Node, abc.ABC):
    """
    A control flow step, i.e. an object the execution of which changes modifies the control flow state.
    """
    pass


class Nop(Statement):
    """
    A statement that does nothing.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class ExpressionStatement(Statement):
    """
    A statement that consists in evaluating an expression.
    """
    def __init__(self, expression, **kwargs):
        """
        Creates a new expression statement.
        :param expression: The expression to be evaluated in this statement.
        :param kwargs: See Statement constructor.
        """
        super().__init__(expression, **kwargs)

    @property
    def expression(self):
        """
        The expression to be evaluated in this statement.
        """
        return self.children[0]


class Assignment(Statement):
    """
    An assignment.
    """

    def __init__(self, target, value, **kwargs):
        """
        Creates a new assignment.
        :param target: An assignable expression.
        :param value: The expression the value of which is to be assigned.
        :param kwargs: See Statement constructor.
        """
        super().__init__(check_type(target, AssignableExpression), check_type(value, Expression), **kwargs)

    @property
    def target(self):
        """
        An assignable expression.
        """
        return self.children[0]

    @property
    def value(self):
        """
        The expression the value of which is to be assigned.
        """
        return self.children[1]


class Block(Statement):
    """
    A sequence of statements that are to be executed one after another.
    """

    def __init__(self, statements, **kwargs):
        """
        Creates a new block statement.
        :param statements: The statements in this block.
        :param kwargs: See Statement constructor.
        """
        super().__init__(*(check_type(s, Statement) for s in statements), **kwargs)


class AtomicBlock(Block):
    """
    A block statement the sub-statements of which should be executed without being interrupted by the execution
    of other processes/tasks.
    """
    pass


class Return(Statement):
    """
    A jump back to the call site of the currently executed function.
    """

    def __init__(self, value, **kwargs):
        """
        Creates a new return statement.
        :param value: The expression computing the value that is to be returned.
        :param kwargs: See Statement constructor.
        """
        super().__init__(check_type(value, Expression), **kwargs)


class AtomicStatement(Statement, abc.ABC):
    """
    A statement that does not have any children.
    """
    def __init__(self, **kwargs):
        """
        Creates a new atomic statement.
        :param kwargs: See Statement constructor.
        """
        super().__init__(**kwargs)


class Break(AtomicStatement):
    """
    A statement that jumps out of a loop.
    """
    pass


class Continue(AtomicStatement):
    """
    A statement that jumps to the end of a loop body.
    """
    pass


class While(Statement):
    """
    A while loop.
    """

    def __init__(self, condition, body, **kwargs):
        """
        Creates a new while loop.
        :param guard: The loop condition.
        :param body: The loop body.
        :param kwargs: See statement constructor.
        """
        super().__init__(check_type(condition, Expression), check_type(body, Statement), **kwargs)

    @property
    def condition(self):
        """
        The loop condition.
        """
        return self.children[0]

    @property
    def body(self):
        """
        The loop body.
        """
        return self.children[1]


class ProcedureDefinition(Statement):
    """
    A statement defining a procedure.
    """

    def __init__(self, name, argnames, body, **kwargs):
        """
        Creates a procedure definition.
        :param name: The name of the procedure to be defined.
        :param argnames: The names of the arguments of the procedure to be defined.
        :param body: The body of the procedure.
        :param kwargs: See statement constructor.
        """
        super().__init__(check_type(name, Identifier), *(check_type(n, Identifier) for n in argnames),
                         check_type(body, Statement), **kwargs)

    @property
    def name(self):
        """
        The name of the procedure being defined.
        """
        return self.children[0]

    @property
    def argnames(self):
        """
        The names of the arguments of the procedure to be defined.
        """
        return self.children[1:-1]

    @property
    def body(self):
        """
        The body of the procedure being defined.
        """
        return self.children[-1]

class ClassDefinition(Statement):
    """
     A statement defining a class.
     """

    def __init__(self, name, bases, body, **kwargs):
        """
        Creates a procedure definition.
        :param name: The name of the procedure to be defined.
        :param argnames: The names of the arguments of the procedure to be defined.
        :param body: The body of the procedure.
        :param kwargs: See statement constructor.
        """
        super().__init__(check_type(name, Identifier), *(check_type(b, Identifier) for b in bases),
                         check_type(body, Statement), **kwargs)

    @property
    def name(self):
        """
        The name of the procedure being defined.
        """
        return self.children[0]

    @property
    def bases(self):
        """
        The names of the arguments of the procedure to be defined.
        """
        return self.children[1:-1]

    @property
    def body(self):
        """
        The body of the procedure being defined.
        """
        return self.children[-1]
