import abc
from abc import ABC
from enum import Enum
from weakref import WeakValueDictionary

from engine.core.exceptions import VCancellationError, VRuntimeError, VException
from engine.core.interaction import Interaction, InteractionState, i2s
from engine.core.machine import TaskStatus, TaskState
from engine.core.none import VNone
from engine.core.primitive import VBool, VInt, VFloat, VStr
from engine.core.procedure import Procedure
from engine.core.property import Property, OrdinaryProperty
from engine.core.type import Type
from engine.core.value import Value
from engine.stack.exceptions import VTypeError
from engine.stack.instructionset import Update, Push, Pop
from engine.stack.procedure import StackProcedure
from engine.stack.program import StackProgram, ProgramLocation
from engine.stack.reference import Reference
from engine.stack.state import StackState
from engine.stack.term import Term
from lang.spek.data.bound import BoundProcedure
from lang.spek.data.cells import VCell
from lang.spek.data.classes import Class
from lang.spek.data.exceptions import VJumpError, VAttributeError
from lang.spek.data.futures import VFuture, FutureStatus
from lang.spek.data.references import FieldReference, NameReference, FrameReference, ReturnValueReference
from lang.spek.data.values import VTuple, VList, VDict, VNamespace
from util import check_type, check_types


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
        self._value = check_type(value, Value).clone_unsealed().seal()

    def hash(self):
        return hash(self._value)

    def equals(self, other):
        return isinstance(other, CTerm) and self._value == other._value

    def evaluate(self, tstate, mstate):
        return self._value

    def print(self, out):
        self._value.print(out)


class TRef(CTerm):
    """
    A term that represents a reference.
    """

    def __init__(self, r):
        """
        Instantiates a constant reference.
        :param r: The reference to be represented by this term.
        """
        super().__init__(check_type(r, Reference))


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
    A term that represents a float constant.
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
        super().__init__(VBool(value))


class CNone(CTerm):
    """
    A term that represents the None constant.
    """

    def __init__(self):
        """
        Instantiates a new None term.
        """
        super().__init__(VNone.instance)


class CString(CTerm):
    """
    A term that represents a character string.
    """

    def __init__(self, value):
        """
        Instantiates a new string constant term.
        :param value: The string this term is supposed to represent.
        """
        super().__init__(VStr(value))


class CType(CTerm):
    """
    A term that represents a fixed type.
    """

    def __init__(self, t):
        """
        Instantiates a new constant type term.
        :param t: The type this term is supposed to represent.
        """
        super().__init__(t)


def print_child(out, parent, child):
    """
    In the process of formatting a parent term, formats one of the parent's children with or without parentheses,
    depending on the operator precedences of parent and child.
    :param out: The io.TextIOBase object to which strings should be written.
    :param parent: A term object the formatting of which has already begun.
    :param child: A term object that is a direct child of the given parent term and that needs to be formatted
                  as part of formatting the parent.
    """

    def level(term):
        if len(term.children) == 0:
            return 0
        elif isinstance(term, ArithmeticBinaryOperation):
            if term.operator == ArithmeticBinaryOperator.POWER:
                return 2
            elif term.operator in (ArithmeticBinaryOperator.TIMES, ArithmeticBinaryOperator.OVER,
                                   ArithmeticBinaryOperator.INTOVER, ArithmeticBinaryOperator.MODULO):
                return 4
            elif term.operator in (ArithmeticBinaryOperator.PLUS, ArithmeticBinaryOperator.MINUS):
                return 5
        elif isinstance(term, UnaryOperation):
            if term.operator == UnaryOperator.MINUS:
                return 3
            elif term.operator == UnaryOperator.NOT:
                return 7
        elif isinstance(term, Comparison):
            return 6
        elif isinstance(term, BooleanBinaryOperation):
            if term.operator == BooleanBinaryOperator.AND:
                return 8
            elif term.operator == BooleanBinaryOperator.OR:
                return 9
        else:
            return 1

        raise NotImplementedError(f"Determining the syntactic operator level for a term of type {type(term)}"
                                  f" has not been implemented!")

    parentheses_needed = level(child) > level(parent)

    if parentheses_needed:
        out.write("(")
    child.print(out)
    if parentheses_needed:
        out.write(")")


class UnaryOperator(Enum):
    """
    A unary operator.
    """
    NOT = 0
    INVERT = 1
    MINUS = 2


class UnaryOperation(Term):
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
        self._op = check_type(op, UnaryOperator)

    def hash(self):
        return hash(self._op)

    def equals(self, other):
        return isinstance(other, UnaryOperation) and self._op == other._op and self.operand == other.operand

    def print(self, out):
        out.write({UnaryOperator.NOT: "not ", UnaryOperator.MINUS: "-"}[self._op])
        print_child(out, self, self.operand)

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
        try:
            if self._op == UnaryOperator.NOT:
                return VBool(not bool(r))
            elif self._op == UnaryOperator.INVERT:
                return ~r
            elif self._op == UnaryOperator.MINUS:
                return -r
            else:
                raise NotImplementedError()
        except TypeError as tex:
            raise VTypeError(f"Cannot apply {self._op} on value of type {r.type}!") from tex


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

    def hash(self):
        return hash(self._op)

    def equals(self, other):
        return isinstance(other, BinaryTerm) and self._op == other._op and tuple(self.children) == tuple(other.children)

    @abc.abstractmethod
    def print_operator(self, out):
        """
        Prints a string reprentation of the binary operator used in this operation.
        :param out: The TextIOBase instance to which the operator should be printed.
        """
        pass

    def print(self, out):
        print_child(out, self, self.left)
        out.write(" ")
        self.print_operator(out)
        out.write(" ")
        print_child(out, self, self.right)

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

    def print_operator(self, out):
        out.write({ArithmeticBinaryOperator.PLUS: "+",
                   ArithmeticBinaryOperator.MINUS: "-",
                   ArithmeticBinaryOperator.TIMES: "*",
                   ArithmeticBinaryOperator.OVER: "/",
                   ArithmeticBinaryOperator.INTOVER: "//",
                   ArithmeticBinaryOperator.MODULO: "%",
                   ArithmeticBinaryOperator.POWER: "**"}[self._op])

    def evaluate(self, tstate, mstate):
        left = self.left.evaluate(tstate, mstate)
        right = self.right.evaluate(tstate, mstate)

        try:
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
        except TypeError as te:
            raise VTypeError(f"Cannot apply {self.operator} on arguments of type ({left.type}, {right.type})") from te


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

    def print_operator(self, out):
        out.write({BooleanBinaryOperator.AND: "and",
                   BooleanBinaryOperator.OR: "or"}[self._op])

    def evaluate(self, tstate, mstate):
        left = self.left.evaluate(tstate, mstate)

        try:
            if self.operator == BooleanBinaryOperator.AND:
                return left and self.right.evaluate(tstate, mstate)
            elif self.operator == BooleanBinaryOperator.OR:
                return left or self.right.evaluate(tstate, mstate)
            else:
                raise NotImplementedError()
        except TypeError as te:
            raise VTypeError(f"Cannot apply {self.operator} on arguments of type ({left.type}, {self.right.evaluate(tstate, mstate)})") from te


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

    def print_operator(self, out):
        out.write({ComparisonOperator.EQ: "==",
                   ComparisonOperator.NEQ: "!=",
                   ComparisonOperator.LESS: "<",
                   ComparisonOperator.LESSOREQUAL: "<=",
                   ComparisonOperator.GREATER: ">",
                   ComparisonOperator.GREATEROREQUAL: ">=",
                   ComparisonOperator.IN: "in",
                   ComparisonOperator.NOTIN: "not in",
                   ComparisonOperator.IS: "is",
                   ComparisonOperator.ISNOT: "is not"}[self._op])

    def evaluate(self, tstate, mstate):
        left = self.left.evaluate(tstate, mstate)
        right = self.right.evaluate(tstate, mstate)

        try:
            if self.operator == ComparisonOperator.EQ:
                return VBool.from_bool(left.cequals(right))
            elif self.operator == ComparisonOperator.NEQ:
                return VBool.from_bool(not left.cequals(right))
            elif self.operator == ComparisonOperator.LESS:
                return VBool.from_bool(left < right)
            elif self.operator == ComparisonOperator.LESSOREQUAL:
                return VBool.from_bool(left <= right)
            elif self.operator == ComparisonOperator.GREATER:
                return VBool.from_bool(left > right)
            elif self.operator == ComparisonOperator.GREATEROREQUAL:
                return VBool.from_bool(left >= right)
            elif self.operator == ComparisonOperator.IN:
                return VBool.from_bool(left in right)
            elif self.operator == ComparisonOperator.NOTIN:
                return VBool.from_bool(left not in right)
            elif self.operator == ComparisonOperator.IS:
                return VBool.from_bool(left is right)
            elif self.operator == ComparisonOperator.ISNOT:
                return VBool.from_bool(left is not right)
            else:
                raise NotImplementedError()
        except TypeError as te:
            raise VTypeError(f"Cannot apply {self.operator} on arguments of type ({left.type}, {self.right.evaluate(tstate, mstate)})") from te


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

    def hash(self):
        return hash(self._p)

    def equals(self, other):
        return isinstance(other, UnaryPredicateTerm) and self._p == other._p and self.operand == other.operand

    def print(self, out):
        out.write({UnaryPredicate.ISCALLABLE: "is_callable",
                   UnaryPredicate.ISEXCEPTION: "is_exception",
                   UnaryPredicate.ISTERMINATED: "is_terminated"}[self._p])
        out.write("(")
        self.operand.print(out)
        out.write(")")

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
            value = isinstance(r, (Procedure, Type))
        elif self._p == UnaryPredicate.ISEXCEPTION:
            value = t.subtypeof(VException.intrinsic_type)
        elif self._p == UnaryPredicate.ISTERMINATED:
            # Check if the argument is a completed available.
            if isinstance(r, TaskState):
                value = r.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED)
            elif isinstance(r, VFuture):
                value = r.status != FutureStatus.UNSET
            else:
                raise VTypeError(f"The argument evaluated to a {type(r)}, which is not supported by ISTERMINATED!")
        else:
            raise NotImplementedError()

        return VBool(value)


class AwaitedResult(Term):
    """
    A term that retrieves the result computed for an awaitable object.
    """

    def __init__(self, t):
        """
        Creates a new AwaitedResult term.
        :param t: A Term evaluating to the awaitable whose result should be read.
        """
        super().__init__(t)

    def hash(self):
        return hash(self.awaited) ^ 56

    def equals(self, other):
        return isinstance(other, AwaitedResult) and self.awaited == other.awaited

    def print(self, out):
        out.write("result(")
        self.awaited.print(out)
        out.write(")")

    @property
    def awaited(self):
        """
        A Term evaluating to the awaitable whose result should be read.
        """
        return self.children[0]

    def evaluate(self, tstate, mstate):
        a = self.awaited.evaluate(tstate, mstate)
        if isinstance(a, StackState):
            if isinstance(a.exception, VCancellationError) and a.exception.initial:
                raise VCancellationError(initial=False, msg="The awaited task has been cancelled!")
            if isinstance(a.exception, Exception):
                raise a.exception
            if a.status != TaskStatus.COMPLETED:
                raise VRuntimeError("Cannot retrieve the result for a task that has not been completed!")
            return VNone.instance if a.returned is None else a.returned
        elif isinstance(a, TaskState):
            if a.status == TaskStatus.COMPLETED:
                return VNone.instance
            else:
                raise VRuntimeError("Cannot retrieve the result for a task that has not been completed!")
        elif isinstance(a, VFuture):
            return a.result
        else:
            raise VTypeError(f"Cannot obtain the result of a {type(a)}!")


class New(Term):
    """
    A term that creates new instances of types.
    """

    def __init__(self, type, *args):
        """
        Creates a new New term.
        :param type: A term evaluating to a Type object, representing the type constructor to call.
        :param args: An iterable of terms evaluating to constructor arguments.
        """
        super().__init__(type, *args)

    @property
    def type(self):
        """
        A term evaluating to a Type object, representing the type constructor to call.
        """
        return self.children[0]

    @property
    def args(self):
        """
        An iterable of terms evaluating to constructor arguments.
        """
        return self.children[1:]

    def hash(self):
        return hash(self.type)

    def equals(self, other):
        return isinstance(other, New) and self.children == other.children

    def print(self, out):
        out.write("new<")
        self.type.print(out)
        out.write(">(")
        prefix = ", "
        for a in self.args:
            out.write(prefix)
            a.print(out)
            prefix = ", "
        out.write(")")

    def evaluate(self, tstate, mstate):
        t = self.type.evaluate(tstate, mstate)
        if not isinstance(t, Type):
            raise VTypeError(f"Only types have constructors, but {t} is not a type!")
        args = tuple(check_types((a.evaluate(tstate, mstate) for a in self.args), Value))
        return t.new(*args)


class Callable(Term):
    """
    A term that converts its argument to a Procedure object, which can be used with a Push or Launch instruction.
    """

    __constructors = WeakValueDictionary()

    def __init__(self, t):
        """
        Creates a new Callable term.
        :param t: A Term evaluating to the object that is to be converted to a callable.
        """
        super().__init__(t)

    def hash(self):
        return hash(self.term) ^ 784658

    def equals(self, other):
        return isinstance(other, Callable) and self.term == other.term

    def print(self, out):
        out.write("callable(")
        self.term.print(out)
        out.write(")")

    @property
    def term(self):
        """
        A Term evaluating to the object that is to be converted to a callable.
        """
        return self.children[0]

    def evaluate(self, tstate, mstate):
        callee = self.term.evaluate(tstate, mstate)

        while True:
            if isinstance(callee, Procedure):
                break
            elif isinstance(callee, Type):
                num_cargs = callee.num_cargs
                try:
                    return BoundProcedure(Callable.__constructors[num_cargs], callee)
                except KeyError:

                    r = TRef(ReturnValueReference())
                    t = TRef(FrameReference(0))
                    args = [TRef(FrameReference(1 + idx)) for idx in range(num_cargs)]

                    c = [Update(r, New(t, *args), 1, 2),
                         Push(Project(LoadAttrCase(r, "__init__"), 1), args, 2, 2),
                         Pop(2)
                         ]

                    c = StackProcedure(1 + t.num_cargs, StackProgram(c))

                    Callable.__constructors[num_cargs] = c
                    return BoundProcedure(c, callee)
            else:
                raise VTypeError(f"Value of type {type(callee)} is not callable!")

        return callee


class ITask(Term):
    """
    A term that retrieves an InteractionStask for a given interaction symbol.
    """

    def __init__(self, s):
        """
        Creates a new interaction task retrieval term.
        :param s: The Interaction symbol to retrieve a task for.
        """
        super().__init__()
        self._s = check_type(s, Interaction)

    def hash(self):
        return hash(self._s) ^ 986573

    def equals(self, other):
        return isinstance(other, ITask) and self._s == other._s

    def print(self, out):
        out.write(f"itask({i2s(self._s)})")

    @property
    def predicate(self):
        """
        The interaction symbol to retrieve a task for.
        """
        return self._s

    def evaluate(self, tstate, mstate):
        t = None
        for task_state in mstate.task_states:
            if isinstance(task_state, InteractionState) and task_state.interaction == self._s:
                if t is not None:
                    raise RuntimeError("There is more than one interaction state for the interaction symbol {}!".format(self._s))
                t = task_state

        if t is None:
            raise RuntimeError("No interaction state could be retrieved for interaction symbol {}!".format(self._s))

        return t


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

    def hash(self):
        return hash(self.types)

    def equals(self, other):
        return isinstance(other, IsInstance) and tuple(self.children) == tuple(other.children)

    def print(self, out):
        out.write("is_instance(")
        self.value.print(out)
        out.write(", ")
        self.types.print(out)
        out.write(")")

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
            return VBool(v.type.subtypeof(t))
        elif isinstance(t, VTuple):
            for tt in t:
                if not isinstance(tt, Type):
                    raise VTypeError("isinstance(() arg 2 must be a type or tuple of types.")
                if v.type.subtypeof(tt):
                    return VBool(True)
            return VBool(False)
        else:
            raise VTypeError("isinstance(() arg 2 must be a type or tuple of types.")


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

    def hash(self):
        return hash(self.reference) ^ 890245

    def equals(self, other):
        return isinstance(other, Read) and tuple(self.children) == tuple(other.children)

    def print(self, out):
        out.write("read(")
        self.reference.print(out)
        out.write(")")

    @property
    def reference(self):
        return self.children[0]

    def evaluate(self, tstate, mstate):
        r = self.reference.evaluate(tstate, mstate)
        if not isinstance(r, Reference):
            raise VTypeError(f"The 'Read' operator cannot be applied to a {r.type}!")
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

    def hash(self):
        return hash(self.index)

    def equals(self, other):
        return isinstance(other, Project) and tuple(self.children) == tuple(other.children)

    def print(self, out):
        print_child(out, self, self.tuple)
        out.write("[")
        self.index.print(out)
        out.write("]")

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
        if not isinstance(t, VTuple):
            raise VTypeError(f"Projection terms only work with tuples not {t.type}!")
        i = self.index.evaluate(tstate, mstate)
        if not isinstance(i, VInt):
            raise VTypeError(f"Projection terms only accept integer indices, not {i.type}!")
        return t[i]


class Lookup(Term):
    """
    A term that constructs a NameReference.
    """
    def __init__(self, namespace, name):
        """
        Creates a new namespace lookup.
        :param namespace: A term evaluating to a reference to a Namespace value.
        :param name: A term specifying the string name that is to be looked up.
        """
        super().__init__(check_type(namespace, Term), check_type(name, Term))

    def hash(self):
        return hash(self.name)

    def equals(self, other):
        return isinstance(other, Lookup) and tuple(self.children) == tuple(other.children)

    def print(self, out):
        print_child(out, self, self.namespace)
        out.write("[")
        self.name.print(out)
        out.write("]")

    @property
    def namespace(self):
        """
        A term evaluating to name space that is to be queried.
        """
        return self.children[0]

    @property
    def name(self):
        """
        A term evaluating to the string name that is to be looked up.
        """
        return self.children[1]

    def evaluate(self, tstate, mstate):
        namespace = self.namespace.evaluate(tstate, mstate)
        name = self.name.evaluate(tstate, mstate)
        try:
            return NameReference(namespace, str(name))
        except TypeError as tex:
            raise VTypeError(str(tex)) from tex


class LoadAttrCase(Term):
    """
    A term that reads an attribute.
    If the given object is of type 'type', then the MRO of the object is searched for the attribute of the given name.
    If the given object is not of type 'type', then the MRO of the type of the object is searched for the attribute.
    In both cases, the term evaluates as follows:
        0. The name was found and refers to a property. The term evaluates to the getter of that property.
        1. The name was found and refers to an instance variable. The term evaluates to the value of the instance variable.
        2. The name was found and refers to a method. The term evaluates to the method.
        3. The name was found and refers to a class variable. The term evaluates to the value of that variable.
        4. The name was not found. The term evaluation raises an exception.

    In case 0, a tuple (True, getter) is returned, and in cases 1, 2 and 3 a tuple (False, value) is returned.

    """

    def __init__(self, value, name):
        """
        Creates a new namespace lookup.
        :param value: A term evaluating to the value an attribute of which should be read.
        :param name: A string specifying the name that is to be looked up.
        """
        super().__init__(check_type(value, Term))
        self._name = check_type(name, str)

    def hash(self):
        return hash(self._name)

    def equals(self, other):
        return isinstance(other, LoadAttrCase) and self._name == other._name and self.value == other.value

    def print(self, out):
        print_child(out, self, self.value)
        out.write(".")
        out.write(self._name)

    @property
    def value(self):
        """
        A term evaluating to the value an attribute of which should be read.
        """
        return self.children[0]

    @property
    def name(self):
        """
        A string specifying the name that is to be looked up.
        """
        return self._name

    def evaluate(self, tstate, mstate):
        value = self.value.evaluate(tstate, mstate)
        t = value.type

        try:
            attr = (value if isinstance(value, Type) else t).members[self.name]
        except KeyError as kex:
            raise VAttributeError(str(kex))
        if isinstance(attr, int):
            return VTuple(VBool.false, value[attr])
        elif isinstance(attr, Procedure):
            return VTuple(VBool.false, BoundProcedure(attr, value))
        elif isinstance(attr, Property):
            return VTuple(VBool.true, BoundProcedure(attr.getter, value))
        else:
            raise VTypeError("The attribute value {value} is of type {value.type}, which LoadAttrCase cannot handle!")


class StoreAttrCase(Term):
    """
    A term that evaluates to a reference that can be written to.
    If the given object is of type 'type', then the MRO of the object is searched for the attribute of the given name.
    If the given object is not of type 'type', then the MRO of the type of the object is searched for the attribute.
    The return value distinguishes the following cases:
        0. The name was found and refers to a property. The term evaluates to the setter of that property.
        1. The name was found and refers to an instance variable. The term valuates to a FieldReference.
        2. The name was found and refers to a method. The term evaluates to an exception to raise.
        3. The name was found and refers to a class variable. The term evaluates to a NameReference.
        4. The name was not found. The term evaluates to an exception to raise.
    """

    def __init__(self, value, name):
        """
        Creates a new namespace lookup.
        :param value: A term evaluating to the value an attribute of which should be written.
        :param name: A string specifying the name that is to be looked up.
        """
        super().__init__(check_type(value, Term))
        self._name = check_type(name, str)

    def hash(self):
        return hash(self._name)

    def equals(self, other):
        return isinstance(other, StoreAttrCase) and self._name == other._name and self.value == other.value

    def print(self, out):
        print_child(out, self, self.value)
        out.write(".")
        out.write(self._name)

    @property
    def value(self):
        """
        A term evaluating to the value an attribute of which should be written.
        """
        return self.children[0]

    @property
    def name(self):
        """
        A string specifying the name that is to be looked up.
        """
        return self._name

    def evaluate(self, tstate, mstate):
        value = self.value.evaluate(tstate, mstate)
        t = value.type

        try:
            attr = (value if isinstance(value, Type) else t).members[self.name]
        except KeyError as kex:
            raise VAttributeError(str(kex))
        if isinstance(attr, int):
            return FieldReference(value, attr)
        if isinstance(attr, Property):
            return attr.setter
        elif isinstance(attr, Procedure):
            return VTypeError("Cannot assign values to method fields!")
        else:
            raise VTypeError("The attribute value {value} is of type {value.type}, which StoreAttrCase cannot handle!")


class NewTuple(Term):
    """
    A term that evaluates to a tuple.
    """

    def __init__(self, *comps):
        """
        Creates a new tuple term.
        :param comps: The terms that evaluate to the components of the tuple.
        """
        super().__init__(*comps)

    def hash(self):
        return len(self.children)

    def equals(self, other):
        return isinstance(other, NewTuple) and tuple(self.children) == tuple(other.children)

    def print(self, out):
        out.write("(")
        prefix = ""
        for c in self.children:
            out.write(prefix)
            c.print(out)
            prefix = ", "
        out.write(")")

    @property
    def components(self):
        """
        The terms that evaluate to the components of the tuple.
        :return:
        """
        return self.children

    def evaluate(self, tstate, mstate):
        return VTuple(*(c.evaluate(tstate, mstate) for c in self.components))


class NewCell(Term):
    """
    A term that evaluates to a new VCell object.
    """

    def __init__(self, term=None):
        """
        Creates a NewCell term.
        :param term: A term that is evaluated to initialize the value of the cell.
        """
        if term is None:
            super().__init__()
        else:
            super().__init__(term)

    @property
    def term(self):
        """
        A term that is evaluated to initialize the value of the cell.
        """
        for t in self.children:
            return t
        return None

    def hash(self):
        return 42

    def equals(self, other):
        return isinstance(other, NewCell) and self.term == other.term

    def print(self, out):
        out.write("NewCell(")
        if self.term is not None:
            self.term.print(out)
        out.write(")")

    def evaluate(self, tstate, mstate):
        return VCell(VNone() if self.term is None else self.term.evaluate(tstate, mstate))


class NewList(Term):
    """
    A term that evaluates to a new empty list.
    """

    def __init__(self):
        """
        Creates a new list term.
        """
        super().__init__()

    def hash(self):
        return 43

    def equals(self, other):
        return isinstance(other, NewList)

    def print(self, out):
        out.write("[]")

    def evaluate(self, tstate, mstate):
        return VList()


class NewDict(Term):
    """
    A term that evaluates to a new empty dictionary.
    """

    def __init__(self):
        """
        Creates a new dict term.
        """
        super().__init__()

    def hash(self):
        return 4711

    def equals(self, other):
        return isinstance(other, NewDict)

    def print(self, out):
        out.write("{}")

    def evaluate(self, tstate, mstate):
        return VDict()


class NewJumpError(Term):
    """
    A term that evaluates to either a break, continue or return exception.
    """

    def __init__(self, etype):
        """
        Creates a new tuple term.
        :param etype: The subclass of VJumpException that is to be instantiated by this term.
        """
        if not issubclass(etype, VJumpError):
            raise TypeError("{} is not a subclass of VJumpException!".format(etype))
        super().__init__()
        self._etype = etype

    def hash(self):
        return 87543

    def equals(self, other):
        return isinstance(other, NewJumpError) and self._etype is other._etype

    def print(self, out):
        out.write(str(self._etype))
        out.write("()")

    @property
    def etype(self):
        """
        The subclass of VJumpException that is to be instantiated by this term.
        """
        return self._etype

    def evaluate(self, tstate, mstate):
        return self._etype()


class NewNamespace(Term):
    """
    A term that evaluates to a new empty namespace.
    """

    def __init__(self):
        """
        Creates a new namespace term.
        """
        super().__init__()

    def hash(self):
        return 1337

    def equals(self, other):
        return isinstance(other, NewNamespace)

    def print(self, out):
        out.write("Namespace()")

    def evaluate(self, tstate, mstate):
        return VNamespace()


class NewProcedure(Term):
    """
    A term that evaluates to a new VProcedure object.
    """

    def __init__(self, num_args, free, entry):
        """
        Creates a new procedure creation term.
        :param num_args: The number of arguments of the procedure to be created by this term.
        :param free: An iterable of terms tha evaluate to values for the free variables of this procedure.
        :param entry: The StackProgram or the ProgramLocation representing the code to be executed by the procedure created by this term.
        """
        super().__init__(*free)
        self._num_args = check_type(num_args, int)
        self._free = check_types(free, Term)
        self._entry = check_type(entry, (ProgramLocation, StackProgram))

    def hash(self):
        return len(self._num_args) ^ hash(self._entry)

    def equals(self, other):
        return (isinstance(other, NewProcedure)
                and self._num_args == other._num_args
                and (self._entry is other._entry or self._entry == other._entry)
                and self._free == other._free)

    def print(self, out):
        out.write("Procedure(")
        out.write(str(self._num_args))
        for f in self._free:
            out.write(", ")
            f.print(out)
        out.write(", ")
        e = self._entry
        if isinstance(e, StackProgram):
            e = ProgramLocation(e, 0)
        e.print(out)
        out.write(")")

    @property
    def num_args(self):
        """
        The number of arguments of the procedure to be created by this term.
        """
        return self._num_args

    @property
    def free(self):
        """
        An iterable of terms evaluating to values that should be part of the constructed procedure object, to represent
        the values of free variables.
        """
        return self._free

    @property
    def entry(self):
        """
        The StackProgram or the ProgramLocation representing the code to be executed by the procedure created by this term.
        """
        return self._entry

    def evaluate(self, tstate, mstate):
        e = self._entry
        if isinstance(e, StackProgram):
            e = ProgramLocation(e, 0)

        return BoundProcedure(StackProcedure(len(self._free) + self._num_args, e),
                              *(f.evaluate(tstate, mstate) for f in self._free))


class NewProperty(Term):
    """
    A term that evaluates to a new VProperty object.
    """

    def __init__(self, getter, setter=None):
        """
        Creates a new procedure creation term.
        :param getter: A term evaluating to a procedure that serves as the getter for the property.
        :param setter: Either None (for a readonly property),
                       or a term evaluating to a procedure that serves as the getter for the property.
        """
        if setter is None:
            super().__init__(getter)
        else:
            super().__init__(getter, setter)

    def hash(self):
        return hash(tuple(self.children))

    def equals(self, other):
        return isinstance(other, NewProperty) and tuple(self.children) == tuple(other.children)

    def print(self, out):
        out.write("Property(")
        self.getter.print(out)
        if self.setter is not None:
            out.write(", ")
            self.setter.print(out)
        out.write(")")

    @property
    def getter(self):
        """
        A term evaluating to a procedure that serves as the getter for the property.
        """
        return self.children[0]

    @property
    def setter(self):
        """
        Either None (for a readonly property),
        or a term evaluating to a procedure that serves as the getter for the property.
        """
        try:
            return self.children[1]
        except IndexError:
            return None

    def evaluate(self, tstate, mstate):
        g = self.getter.evaluate(tstate, mstate)
        s = None if self.setter is None else self.setter.evaluate(tstate, mstate)
        return OrdinaryProperty(g, s)


class NewClass(Term):
    """
    A term that evaluates to a new Type object.
    """

    def __init__(self, name, superclasses, namespace):
        """
        Creates a new Class term.
        :param name: The string name of the class to be created.
        :param superclasses: An iterable of terms that evaluate to super classes
                             of the class to be created by this term.
        :param namespace: A term evaluating to a namespace binding names to members
                          of the class to be created by this term.
        """
        super().__init__(*superclasses, namespace)
        self._name = check_type(name, str)

    def hash(self):
        return hash(self._name)

    def equals(self, other):
        return isinstance(other, NewClass) and self._name == other._name and tuple(self.children) == tuple(other.children)

    def print(self, out):
        out.write("class(")
        out.write(repr(self._name))
        *superclasses, ns = self.children
        out.write(", [")
        prefix = ""
        for s in superclasses:
            out.write(prefix)
            s.print(out)
            prefix = ", "
        out.write("], ")
        ns.print(out)
        out.write(")")

    @property
    def name(self):
        """
        The string name of the class to be created.
        """
        return self._name

    @property
    def superclasses(self):
        """
        An iterable of terms that evaluate to super classes of the class to be created by this term.
        """
        return self.children[:-1]

    @property
    def namespace(self):
        """
        A term evaluating to a namespace binding names to members of the class to be created by this term.
        """
        return self.children[-1]

    def evaluate(self, tstate, mstate):
        ss = tuple(s.evaluate(tstate, mstate) for s in self.superclasses)

        field_names = []
        members = {}
        for name, member in self.namespace.evaluate(tstate, mstate):
            if isinstance(member, (Procedure, Property)):
                members[name] = member
            elif isinstance(member, VNone):
                field_names.append(name)
            else:
                raise VRuntimeError("Encountered an unexpected entry in a namespace to be used for class creation!")

        return Class(self._name, ss, field_names, members)
