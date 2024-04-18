import abc
from abc import ABC
from enum import Enum
from weakref import WeakValueDictionary

from engine.core.atomic import type_object, EmptyMember
from engine.core.compound import FieldIndex
from engine.core.data import VBool, VInt, VFloat, VStr, VException, VCancellationError, VRuntimeError
from engine.core.interaction import Interaction, InteractionState, i2s
from engine.core.machine import TaskStatus, TaskState
from engine.core.none import VNone, value_none
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
from lang.spek.data.builtin import builtin_iter
from lang.spek.data.cells import VCell
from lang.spek.data.classes import Class
from lang.spek.data.empty import EmptyProcedure
from lang.spek.data.exceptions import VJumpError, VAttributeError, JumpType
from lang.spek.data.futures import VFuture, FutureStatus
from lang.spek.data.references import FieldReference, FrameReference, ReturnValueReference, ItemReference, CellReference
from lang.spek.data.values import VTuple, VList, VDict
from util import check_type, check_types
from util.finite import Finite
from util.keyable import Keyable
from util.singleton import Singleton

pt2vt = {int: VInt, float: VFloat, bool: VBool, str: VStr, tuple: VTuple, list: VList, dict: VDict}

def p2v(x):
    """
    Maps Python objects to Value instances.
    :param x: A Python object.
    :return: A Value.
    """
    return x if isinstance(x, Value) else pt2vt[type(x)](x)


class CTerm(Keyable, Term):
    """
    A term that represents a constant value.
    """

    def __new__(cls, value, *largs, **kwargs):
        value = cls.prepare(value)
        assert check_type(value, Value).sealed
        return super().__new__(cls, value, *largs, **kwargs)

    def __init__(self, value):
        """
        Wraps a value as a Term.
        :param value: The value to wrap.
        """
        # Keyable.__new__ already consumed the value.
        super().__init__()

    @classmethod
    def prepare(cls, value):
        """
        Turns the given object into a sealed Value object.
        :param value: An object.
        :return: A sealed Value object.
        """
        return check_type(value, Value).clone_unsealed().seal()

    def evaluate(self, tstate, mstate):
        return self.instance_key

    def print(self, out):
        self.instance_key.print(out)


class CRef(CTerm):
    """
    A term that represents a reference.
    """
    @classmethod
    def prepare(cls, value):
        return check_type(value, Reference).clone_unsealed().seal()


class CInt(CTerm):
    """
    A term that represents an integer constant.
    """
    @classmethod
    def prepare(cls, value):
        return VInt(check_type(value, int))


class CFloat(CTerm):
    """
    A term that represents a float constant.
    """
    @classmethod
    def prepare(cls, value):
        return VFloat(check_type(value, float))


class CBool(Finite, CTerm):
    """
    A term that represents a boolean constant.
    """

    def __new__(cls, value, *args, **kwargs):
        return super().__new__(cls, value, value, *args, **kwargs)

    @classmethod
    def prepare(cls, value):
        return VBool(bool(value))


class CNone(Singleton, CTerm):
    """
    A term that represents the None constant.
    """

    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, value_none, *args, **kwargs)

    def __init__(self):
        """
        Instantiates a new None term.
        """
        super().__init__(value_none)

    @classmethod
    def prepare(cls, value):
        return value_none


class CString(CTerm):
    """
    A term that represents a character string.
    """
    @classmethod
    def prepare(cls, value):
        return VStr(check_type(value, str))


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
        try:
            r = check_type(self.operand.evaluate(tstate, mstate), Value)

            if self._op == UnaryOperator.NOT:
                return p2v(not r.__python__())
            elif self._op == UnaryOperator.INVERT:
                return p2v(~r.__python__())
            elif self._op == UnaryOperator.MINUS:
                return p2v(-r.__python__())
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
                return p2v(left + right)
            elif self.operator == ArithmeticBinaryOperator.MINUS:
                return p2v(left - right)
            elif self.operator == ArithmeticBinaryOperator.TIMES:
                try:
                    r = left * right
                except TypeError:
                    r = right * left
                return p2v(r)
            elif self.operator == ArithmeticBinaryOperator.OVER:
                return p2v(left / right)
            elif self.operator == ArithmeticBinaryOperator.INTOVER:
                return p2v(left // right)
            elif self.operator == ArithmeticBinaryOperator.MODULO:
                return p2v(left % right)
            elif self.operator == ArithmeticBinaryOperator.POWER:
                return p2v(left ** right)
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
        try:
            left = check_type(self.left.evaluate(tstate, mstate), VBool).__python__()
            if self.operator == BooleanBinaryOperator.AND:
                return VBool(left and check_type(self.right.evaluate(tstate, mstate), VBool).__python__())
            elif self.operator == BooleanBinaryOperator.OR:
                return VBool(left or check_type(self.right.evaluate(tstate, mstate), VBool).__python__())
            else:
                raise NotImplementedError()
        except TypeError as te:
            raise VTypeError(f"Cannot apply {self.operator} on arguments of type ({left.type}, {self.right.evaluate(tstate, mstate).type})") from te


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
                return VBool(left.cequals(right))
            elif self.operator == ComparisonOperator.NEQ:
                return VBool(not left.cequals(right))
            elif self.operator == ComparisonOperator.LESS:
                return VBool(left < right)
            elif self.operator == ComparisonOperator.LESSOREQUAL:
                return VBool(left <= right)
            elif self.operator == ComparisonOperator.GREATER:
                return VBool(left > right)
            elif self.operator == ComparisonOperator.GREATEROREQUAL:
                return VBool(left >= right)
            elif self.operator == ComparisonOperator.IN:
                return VBool(left in right)
            elif self.operator == ComparisonOperator.NOTIN:
                return VBool(left not in right)
            elif self.operator == ComparisonOperator.IS:
                return VBool(left is right)
            elif self.operator == ComparisonOperator.ISNOT:
                return VBool(left is not right)
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
    ISRETURN = 3
    ISBREAK = 4
    ISCONTINUE = 5


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
        elif self._p == UnaryPredicate.ISRETURN:
            value = isinstance(r, VJumpError) and r.reason == JumpType.RETURN
        elif self._p == UnaryPredicate.ISBREAK:
            value = isinstance(r, VJumpError) and r.reason == JumpType.BREAK
        elif self._p == UnaryPredicate.ISCONTINUE:
            value = isinstance(r, VJumpError) and r.reason == JumpType.CONTINUE
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
            return value_none if a.returned is None else a.returned
        elif isinstance(a, TaskState):
            if a.status == TaskStatus.COMPLETED:
                return value_none
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
        prefix = ""
        for a in self.args:
            out.write(prefix)
            a.print(out)
            prefix = ", "
        out.write(")")

    def evaluate(self, tstate, mstate):
        t = self.type.evaluate(tstate, mstate)
        if not isinstance(t, Type):
            raise VTypeError(f"Only types have constructors, but {t} is not a type!")
        args = check_types((a.evaluate(tstate, mstate) for a in self.args), Value)
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

                    r = CRef(ReturnValueReference())
                    t = Read(CRef(FrameReference(0)))
                    args = [Read(CRef(FrameReference(1 + idx))) for idx in range(num_cargs)]

                    c = [Update(r, New(t, *args), 1, 2),
                         Push(Read(Project(LoadAttrCase(Read(r), "__init__"), CInt(1))), args, 2, 2),
                         Pop(2)
                         ]

                    c = StackProcedure(1 + callee.num_cargs, ProgramLocation(StackProgram(c), 0))

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


class Read(Keyable, Term):
    """
    A term that resolves a Reference value.
    """

    def __init__(self, r):
        """
        Creates a new Read term.
        :param r: A term specifying the reference to be read.
        """
        super().__init__(r)

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
    A projecting a data structure to one of its components. Evaluating this term yields an ItemReference.
    """

    def __init__(self, structure, index):
        """
        Creates a new projection term.
        :param structure: A term evaluating to a Value that is to be projected.
        :param index: A term evaluating to a Value that is to be used as a key to index the data structure.
        """
        super().__init__(structure, index)

    def hash(self):
        return hash(self.structure) ^ hash(self.index)

    def equals(self, other):
        return isinstance(other, Project) and self.children == other.children

    def print(self, out):
        print_child(out, self, self.structure)
        out.write("[")
        self.index.print(out)
        out.write("]")

    @property
    def structure(self):
        """
        A term evaluating to a Value that is to be projected.
        """
        return self.children[0]

    @property
    def index(self):
        """
        A term evaluating to a Value that is to be used as a key to index the data structure.
        """
        return self.children[1]

    def evaluate(self, tstate, mstate):
        return ItemReference(self.structure.evaluate(tstate, mstate), self.index.evaluate(tstate, mstate))


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
        bound = not isinstance(value, Type)

        if value.type is type_object and self.name == "__init__":
            return VTuple((VBool(False), EmptyProcedure()))
        try:
            attr = (value.type if bound else value).members[self.name]
        except KeyError as kex:
            raise VAttributeError(str(kex))
        if isinstance(attr, FieldIndex):
            return VTuple((VBool(False), value[int(attr)] if bound else attr))
        elif isinstance(attr, EmptyMember):
            return VTuple((VBool(False), EmptyProcedure()))
        elif isinstance(attr, Procedure):
            return VTuple((VBool(False), BoundProcedure(attr, value) if bound else attr))
        elif isinstance(attr, Property):
            return VTuple((VBool(True), BoundProcedure(attr.getter, value) if bound else attr.getter))
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
        3. The name was found and refers to a class variable. The term evaluates to a ItemReference.
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
        bound = not isinstance(value, Type)

        try:
            attr = (value.type if bound else value).members[self.name]
        except KeyError as kex:
            raise VAttributeError(str(kex))
        if isinstance(attr, FieldIndex):
            return FieldReference(value, int(attr)) if bound else attr
        if isinstance(attr, Property):
            return BoundProcedure(attr.setter, value) if bound else attr.setter
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
        return VTuple((c.evaluate(tstate, mstate) for c in self.components))


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
        return VCell(value_none if self.term is None else self.term.evaluate(tstate, mstate))


class NewList(Term):
    """
    A term that evaluates to a new list object.
    """

    def __init__(self, *elements):
        """
        Creates a new list term.
        :param elements: The terms that evaluate to the components of the tuple.
        """
        super().__init__(*elements)

    def hash(self):
        return len(self.children)

    def equals(self, other):
        return isinstance(other, NewList) and tuple(self.children) == tuple(other.children)

    def print(self, out):
        out.write("[")
        prefix = ""
        for c in self.children:
            out.write(prefix)
            c.print(out)
            prefix = ", "
        out.write("]")

    @property
    def elements(self):
        """
        The terms that evaluate to the elements of the list.
        :return:
        """
        return self.children

    def evaluate(self, tstate, mstate):
        return VList((c.evaluate(tstate, mstate) for c in self.elements))


class NewDict(Term):
    """
    A term that evaluates to a new VDict object.
    """

    def __init__(self, items):
        """
        Creates a new dict term.
        :param items: An iterable of pairs of terms that define the items of the dictionary.
        """
        super().__init__(*(x for kv in items for x in kv))

    def hash(self):
        return len(self.children) // 2

    def print(self, out):
        out.write("{")
        prefix = ""
        for k, v in self.items:
            out.write(prefix)
            k.print(out)
            out.write(": ")
            v.print(out)
            prefix = ", "
        out.write("}")

    def equals(self, other):
        return isinstance(other, NewDict) and tuple(self.children) == tuple(other.children)

    @property
    def items(self):
        """
        The terms that define the items of the dictionary.
        :return: An iterable of pairs (k, v).
        """
        return zip(self.children[::2], self.children[1::2])

    def evaluate(self, tstate, mstate):
        return VDict(((k.evaluate(tstate, mstate), v.evaluate(tstate, mstate)) for k, v in self.items))


class NewJumpError(Finite, Term):
    """
    A term that evaluates to either a break, continue or return exception.
    """

    def __init__(self, reason):
        """
        Creates a new tuple term.
        :param reason: The JumpType justifying the error to create.
        """
        super().__init__()
        self._reason = check_type(reason, JumpType)

    def print(self, out):
        out.write(f"JumpError({self._reason})")

    @property
    def reason(self):
        """
        The JumpType justifying the error to create.
        """
        return self._reason

    def evaluate(self, tstate, mstate):
        return VJumpError(self._reason)


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
        return isinstance(other, NewClass) and self._name == other._name and self.children == other.children

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
        for name, member in check_type(self.namespace.evaluate(tstate, mstate), VDict).items():
            if isinstance(member, (Procedure, Property)):
                members[name] = member
            elif isinstance(member, VNone):
                field_names.append(str(name))
            else:
                raise VRuntimeError("Encountered an unexpected entry in a namespace to be used for class creation!")

        return Class(self._name, ss, field_names, members)


class NewCellReference(Term):
    """
    A term that evaluates to a CellReference.
    """

    def __init__(self, ref):
        """
        Creates a new cell reference term.
        :param ref: A term that evaluates to a Reference.
        """
        super().__init__(ref)

    def hash(self):
        return hash(self.core)

    def equals(self, other):
        return isinstance(other, NewCellReference) and self.children == other.children

    def print(self, out):
        out.write("NewCellReference(")
        self.core.print(out)
        out.write(")")

    @property
    def core(self):
        """
        A term that evaluates to a VCell.
        """
        return self.children[0]

    def evaluate(self, tstate, mstate):
        return CellReference(self.core.evaluate(tstate, mstate))


class Iter(Term):
    """
    A term that obtains an iterator for a sequence.
    """

    def __init__(self, iterable):
        """
        Creates a new Iter term.
        :param iterable: A term that evaluates to an iterable, i.e. to an object for which iterators can be obtained.
        """
        super().__init__(iterable)

    @property
    def iterable(self):
        """
        A term that evaluates to an iterable, i.e. to an object for which iterators can be obtained.
        """
        return self.children[0]

    def hash(self):
        return hash(self.iterable)

    def equals(self, other):
        return isinstance(other, Iter) and self.iterable.equals(other.iterable)

    def print(self, out):
        out.write("iter(")
        self.iterable.print(out)
        out.write(")")

    def evaluate(self, tstate, mstate):
        return builtin_iter(self.iterable.evaluate(tstate, mstate))
