import abc
from enum import Enum

from lang.spek.data.terms import UnaryOperator, ComparisonOperator, BooleanBinaryOperator, ArithmeticBinaryOperator
from lang.tokens import TokenPosition
from util import check_type


class Node:
    """
    A node in an abstract syntax tree.
    """

    def __init__(self, *children, start=None, end=None):
        super().__init__()

        for c in children:
            check_type(c, Node)

        self._children = children
        self._start = check_type(start, TokenPosition, allow_none=True)
        self._end = check_type(end, TokenPosition, allow_none=True)

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

    @property
    @abc.abstractmethod
    def assignable(self):
        """
        Indicates if this expression denotes a target for assignments.
        :return: A boolean value.
        """
        pass

    def variables(self):
        """
        An iterable of the variables occurring in this expression.
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
    def __init__(self, text, start=None, end=None):
        super().__init__(start=start, end=end)
        self._text = check_type(text, str)

    @property
    def assignable(self):
        return False

    @property
    def text(self):
        """
        The text representation of this constant.
        """
        return self._text


class Identifier(Expression):
    """
    An identifier.
    """

    def __init__(self, name, **kwargs):
        """
        Creates a new identifier expression
        :param name: The name of this identifier.
        :param kwargs: See Expression constructor.
        """
        super().__init__(**kwargs)
        self._name = check_type(name, str)

    @property
    def assignable(self):
        return True

    @property
    def name(self):
        """
        The name of this identifier.
        """
        return self._name

    def __str__(self):
        return f"'{self._name}'"


class Tuple(Expression):
    """
    A tuple expression.
    """
    def __init__(self, *components, **kwargs):
        """
        Creates a new tuple expression.
        :param components: The expressions for the tuple components.
        :param kwargs: See Expression constructor.
        """
        super().__init__(*(check_type(c, Expression) for c in components), **kwargs)

    @property
    def assignable(self):
        return all(c.assignable for c in self.children)


class List(Expression):
    """
    A list literal.
    """
    def __init__(self, *elements, **kwargs):
        """
        Creates a new list expression.
        :param elements: The expressions for the list elements.
        :param kwargs: See Expression constructor.
        """
        super().__init__(*(check_type(c, Expression) for c in elements), **kwargs)

    @property
    def assignable(self):
        return all(c.assignable for c in self.children)


class Dict(Expression):
    """
    A dict literal.
    """
    def __init__(self, items, **kwargs):
        """
        Creates a new dict expression.
        :param items: An iterable of (key, value) pairs defining the content of the dict denoted by this expression.
        :param kwargs: See Expression constructor.
        """
        super().__init__(*(check_type(x, Expression) for kv in items for x in kv), **kwargs)

    @property
    def items(self):
        """
        An iterable of (key, value) pairs defining the content of the dict denoted by this expression.
        """
        return [(k, v) for k, v in zip(self.children[::2], self.children[1::2])]

    @property
    def assignable(self):
        return all(c.assignable for c in self.children)


class Projection(Expression):
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

    @property
    def assignable(self):
        return True

    @property
    def value(self):
        """
        The expression representing the value to project.
        """
        return self.children[0]

    @property
    def index(self):
        """
        The expression representing the key to which projection should be computed.
        """
        return self.children[1]


class Attribute(Expression):
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
        super().__init__(check_type(value, Expression), check_type(identifier, Identifier), **kwargs)

    @property
    def assignable(self):
        return True

    @property
    def value(self):
        """
        The expression representing the value to retrieve the attribute from.
        """
        return self.children[0]

    @property
    def name(self):
        """
        The name of the attribute to retrieve.
        """
        return self.children[1]


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
    def assignable(self):
        return False

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
    def __init__(self, work, **kwargs):
        """
        Creates a new process launch expression.
        :param work: An expression representing the computation that
                     the newly launched process is supposed to execute.
        :param kwargs: See Expression constructor.
        """
        super().__init__(check_type(work, Expression), **kwargs)

    @property
    def assignable(self):
        return False

    @property
    def work(self):
        """
        The expression that the new process is supposed to evaluate.
        :return: A Call object.
        """
        return self.children[0]


class Await(Expression):
    """
    An expression that waits for an awaitable object, returning its result after blocking until it is available.
    Tasks and futures are awaitable.
    """
    def __init__(self, awaitable, **kwargs):
        """
        Creates a new await expression.
        :param awaitable: An expression representing the awaited result.
        :param kwargs: See Expression constructor.
        """
        super().__init__(check_type(awaitable, Expression), **kwargs)

    @property
    def assignable(self):
        return False

    @property
    def awaited(self):
        """
        An expression representing the awaited result.
        :return: An Expression object.
        """
        return self.children[0]


class UnaryOperation(Expression, abc.ABC):
    """
    An operation with one operand.
    """

    def __init__(self, op, arg, **kwargs):
        """
        Creates a new unary operation.
        :param op: The operator for this operation.
        :param arg: The operand expression.
        :param kwargs: See Expression constructor.
        """
        super().__init__(check_type(arg, Expression), **kwargs)
        self._op = check_type(op, UnaryOperator)

    @property
    def assignable(self):
        return False

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
    def assignable(self):
        return False

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


class Pass(Statement):
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
        if not check_type(target, Expression).assignable:
            raise ValueError("The given target expression is not assignable!")
        super().__init__(target, check_type(value, Expression), **kwargs)

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
        if value is None:
            super().__init__(**kwargs)
        else:
            super().__init__(check_type(value, Expression), **kwargs)

    @property
    def value(self):
        """
        The expression computing the value that is to be returned. May be None.
        """
        try:
            return self.children[0]
        except IndexError:
            return None


class Raise(Statement):
    """
    A statement that raise an exception.
    """

    def __init__(self, value, **kwargs):
        """
        Creates a new raise statement.
        :param value: The expression computing the value that is to be raised.
        :param kwargs: See Statement constructor.
        """
        if value is None:
            super().__init__(**kwargs)
        else:
            super().__init__(check_type(value, Expression), **kwargs)

    @property
    def value(self):
        """
        The expression computing the exception that is to be raised. May be None.
        """
        try:
            return self.children[0]
        except IndexError:
            return None


class Break(Statement):
    """
    A statement that jumps out of a loop.
    """
    pass


class Continue(Statement):
    """
    A statement that jumps to the end of a loop body.
    """
    pass


class Conditional(Statement):
    """
    A statement composed of several conditional alternatives.
    """

    def __init__(self, condition, consequence, alternative, **kwargs):
        """
        Creates a Conditional statement.
        :param condition: The expression to be evaluated in order to decide which statement is to be executed.
        :param consequence: The statement to be executed if the condition was evaluated positively.
        :param alternative: The statement to be executed if the condition was evaluated negatively.
        :param kwargs: See statement constructor.
        """

        if alternative is None:
            super().__init__(check_type(condition, Expression), check_type(consequence, Statement), **kwargs)
        else:
            super().__init__(check_type(condition, Expression),
                             check_type(consequence, Statement),
                             check_type(alternative, Statement), **kwargs)

    @property
    def condition(self):
        """
        The expression to be evaluated in order to decide which statement is to be executed.
        """
        return self.children[0]

    @property
    def consequence(self):
        """
        The statement to be executed if the condition was evaluated positively.
        """
        return self.children[1]

    @property
    def alternative(self):
        """
        The statement to be executed if the condition was evaluated negatively.
        """
        return self.children[2] if len(self.children) > 2 else None


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


class For(Statement):
    """
    A for loop.
    """

    def __init__(self, pattern, iterable, body, **kwargs):
        """
        Creates a new 'for' loop.
        :param pattern: The pattern to which the item for the current iteration should be assigned.
        :param iterable: The expression denoting the iterable to iterate over.
        :param body: The loop body.
        :param kwargs: See statement constructor.
        """
        super().__init__(check_type(pattern, Expression),
                         check_type(iterable, Expression),
                         check_type(body, Statement),
                         **kwargs)

    @property
    def pattern(self):
        """
        The pattern to which the item for the current iteration should be assigned.
        """
        return self.children[0]

    @property
    def iterable(self):
        """
        The expression denoting the iterable to iterate over.
        """
        return self.children[1]

    @property
    def body(self):
        """
        The loop body.
        """
        return self.children[2]


class Except(Node):
    """
    An except clause for a try-statement.
    """
    def __init__(self, type, name, body, **kwargs):
        """
        Creates a new 'except' clause.
        :param type: The expression denoting the type of the exception to catch.
        :param name: The name to which the exception that was caught should be assigned.
        :param body: The statement to execute in order to handle the exception.
        :param kwargs: See Node constructor.
        """

        children = []

        if type is not None:
            children.append(check_type(type, Expression))

        if name is not None:
            children.append(check_type(name, Identifier))

        children.append(check_type(body, Statement))

        super().__init__(*children, **kwargs)

    @property
    def type(self):
        """
        The expression denoting the type of the exception to catch.
        """
        if len(self.children) == 1:
            return None
        else:
            return self.children[0]

    @property
    def identifier(self):
        """
        The name to which the exception that was caught should be assigned.
        """
        if len(self.children) < 3:
            return None
        elif len(self.children) == 3:
            return self.children[1]
        else:
            raise Exception("Unexpected number of children in an Except node!")

    @property
    def body(self):
        """
        The statement to execute in order to handle the exception.
        """
        return self.children[-1]


class Try(Statement):
    """
    A try statement.
    """

    def __init__(self, body, handlers, final, **kwargs):
        """
        Creates a new try statement.
        :param body: The code block that may raise exceptions.
        :param handlers: An iterable of Except objects.
        :param final: The code block to be executed when control leaves the try statement.
        :param kwargs: See statement constructor.
        """

        children = [check_type(body, Statement)]

        for h in handlers:
            children.append(check_type(h, Except))

        if final is not None:
            children.append(check_type(final, Statement))

        super().__init__(*children, **kwargs)

    @property
    def body(self):
        """
        The code block that may raise exceptions.
        """
        return self.children[0]

    @property
    def handlers(self):
        """
        The Except objects defining how to handle exceptions.
        """
        return self.children[1:] if self.final is None else self.children[1:-1]

    @property
    def final(self):
        """
        The code block to be executed when control leaves the try statement.
        """
        return None if isinstance(self.children[-1], Except) else self.children[-1]


class VariableDeclaration(Statement):
    """
     A statement declaring a variable.
     """

    def __init__(self, pattern, expression=None, **kwargs):
        """
        Creates a variable declaration.
        :param pattern: The expression holding the identifiers to be declared.
        :param expression: The expression the evaluation result of which the newly declared variable(s)
                           should be bound to. May be None.
        :param kwargs: See statement constructor.
        """

        if expression is None:
            super().__init__(check_type(pattern, Expression), **kwargs)
        else:
            check_type(expression, Expression)
            super().__init__(check_type(pattern, Expression), expression, **kwargs)

    @property
    def pattern(self):
        """
        The expression holding the identifiers to be declared.
        """
        return self.children[0]

    @property
    def expression(self):
        """
        The expression the evaluation result of which the newly declared variable should be bound to.
        May be None.
        """
        if len(self.children) > 1:
            return self.children[-1]
        else:
            return None


class Source(Node):
    """
    Denotes a source from which to import definitions of names.
    """
    def __init__(self, *identifiers, **kwargs):
        """
        Creates a new import source.
        :param identifiers: A sequence of identifiers that specify the source.
        :param kwargs: See node constructor.
        """
        super().__init__(*(check_type(i, Identifier) for i in identifiers), **kwargs)

    @property
    def identifiers(self):
        """
        The sequence of identifiers that specify the source.
        """
        return self.children


class ImportSource(Statement):
    """
     A statement that makes a source available under a name.
     """

    def __init__(self, source, alias=None, **kwargs):
        """
        Creates an import statement.
        :param source: A Source node.
        :param alias: The alias under which the source should be made available by the import.
        :param kwargs: See statement constructor.
        """

        check_type(source, Source)
        if alias is None:
            super().__init__(source, **kwargs)
        else:
            super().__init__(source, check_type(alias, Identifier), **kwargs)

    @property
    def source(self):
        """
        The source of the import.
        """
        return self.children[0]

    @property
    def alias(self):
        """
        The name under which the source should be made available. May be None.
        """
        return self.children[-1] if len(self.children) > 1 else None


class ImportNames(Statement):
    """
     A statement importing names from other sources.
     """

    def __init__(self, source, name2alias=None, **kwargs):
        """
        Creates an import statement.
        :param source: A Source node.
        :param name2alias: A mapping from names defined in the source to alias names. If omitted, *all* the names defined
                           in the source will be imported.
        :param kwargs: See statement constructor.
        """
        check_type(source, Source)
        if name2alias is None:
            super().__init__(source, **kwargs)
        else:
            super().__init__(source, *(check_type(c, Identifier) for t in name2alias.items() for c in t), **kwargs)

    @property
    def source(self):
        """
        The source of the import.
        """
        return self.children[0]

    @property
    def wildcard(self):
        """
        Indicates if this import is supposed to make all names from the source available in the current environment.
        """
        return len(self.children) == 1

    @property
    def aliases(self):
        """
        A mapping from names to aliases. If this mapping is empty or None, *all* names defined in the source will be
        made available. Otherwise the keys of the mapping will be made available under their values.
        """
        return {self.children[1 + 2 * idx]: self.children[1 + 2 * idx + 1] for idx in range((len(self.children) - 1) // 2)}


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


class PropertyDefinition(Statement):
    """
    A statement defining a getter and (possibly) setter for an instance property.
    """

    def __init__(self, name, gself, getter, sself, vname, setter, **kwargs):
        """
        Creates a procedure definition.
        :param name: The name of the property to be defined.
        :param gself: The identifier for the variable holding the class instance to apply the getter to.
        :param getter: The getter statement of the property.
        :param sself: The identifier for the variable holding the class instance to apply the setter to (may be None).
        :param vname: The identifier for the variable holding the value that is to be written by the setter (may be None)
        :param setter: The setter statement of the property (may be None).
        :param kwargs: See statement constructor.
        """

        if not ((sself is None) == (vname is None) == (setter is None)):
            raise ValueError("The given 'sself' and 'vname' must be None if and only if the given 'setter' is None!")

        if setter is None:
            super().__init__(check_type(name, Identifier), check_type(getter, Statement), **kwargs)
        else:
            super().__init__(check_type(name, Identifier),
                             check_type(gself, Identifier),
                             check_type(getter, Statement),
                             check_type(sself, Identifier),
                             check_type(vname, Identifier),
                             check_type(setter, Statement),
                             **kwargs)

    @property
    def name(self):
        """
        The name of the property being defined.
        """
        return self.children[0]

    @property
    def gself(self):
        """
        The identifier for the variable holding the class instance to apply the getter to.
        """
        return self.children[1]

    @property
    def getter(self):
        """
        The getter statement of the property.
        """
        return self.children[2]

    @property
    def sself(self):
        """
        The identifier for the variable holding the class instance to apply the setter to (may be None).
        """
        try:
            return self.children[-3]
        except IndexError:
            return None

    @property
    def vname(self):
        """
        The identifier for the variable holding the value that is to be written by the setter (may be None)
        """
        try:
            return self.children[-2]
        except IndexError:
            return None

    @property
    def setter(self):
        """
        The setter statement of the property (may be None).
        """
        try:
            return self.children[-1]
        except IndexError:
            return None


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
        if bases is None:
            super().__init__(check_type(name, Identifier), check_type(body, Statement), **kwargs)
        else:
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
