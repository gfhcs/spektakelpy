from abc import ABC
from enum import Enum

from engine.functional.reference import FieldReference
from util import check_type
from . import Reference, EvaluationException, Term, Value, Type
from .values import VInt, VFloat, VBool, VNone, VTuple, VTypeError, VStr, VDict, VNamespace, VProcedure, \
    VProperty, VModule, VAttributeError, VJumpError, VList
from ..task import TaskStatus
from ..tasks.instructions import StackProgram, ProgramLocation
from ..tasks.interaction import Interaction, InteractionState


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

    def __str__(self):
        return str(self._value)

    def evaluate(self, tstate, mstate):
        return self._value


class CRef(CTerm):
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

    def __str__(self):
        op = {ArithmeticUnaryOperator.NOT: "~", ArithmeticUnaryOperator.MINUS: "-"}[self._op]
        arg = self.operand
        return f"{op}{arg}"

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
            return VBool.from_bool(left == right)
        elif self.operator == ComparisonOperator.NEQ:
            return VBool.from_bool(left != right)
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
        from .types import TBuiltin
        r = self.operand.evaluate(tstate, mstate)
        t = r.type
        if self._p == UnaryPredicate.ISCALLABLE:
            # Check if it is a function object, a class object, or if the type of the object has a __call__ method.
            try:
                value = t.subtypeof(TBuiltin.procedure) or isinstance(t.resolve_member("__call__"), VProcedure)
            except KeyError:
                value = False
        elif self._p == UnaryPredicate.ISEXCEPTION:
            # Check if the type of the object is a descendant of TException:
            value = t.subtypeof(TBuiltin.exception)
        elif self._p == UnaryPredicate.ISTERMINATED:
            # Check if the argument is a terminated task
            value = r.status in (TaskStatus.COMPLETED, TaskStatus.FAILED)
        else:
            raise NotImplementedError()

        return VBool(value)


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
        r = self.reference.evaluate(tstate, mstate)
        assert isinstance(r, Reference)
        try:
            return r.read(tstate, mstate)
        except Exception as ex:
            raise EvaluationException("Failed to read from reference!") from ex


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
        :param name: A term specifying the string name that is to be looked up.
        """
        super().__init__(check_type(namespace, Term), check_type(name, Term))

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
        return namespace[name]


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
    """

    def __init__(self, value, name):
        """
        Creates a new namespace lookup.
        :param value: A term evaluating to the value an attribute of which should be read.
        :param name: A string specifying the name that is to be looked up.
        """
        super().__init__(check_type(value, Term))
        self._name = check_type(name, str)

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
            attr = (value if t.subtypeof(Type.instance) else t).resolve_member(self.name)
            if isinstance(attr, int):
                return value[attr]
            elif isinstance(attr, VProperty):
                return attr.getter
            else:
                raise TypeError(type(attr))
        except KeyError:
            return VAttributeError()


class StoreAttrCase(Term):
    """
    A term that evaluates to a reference that can be written to.
    If the given object is of type 'type', then the MRO of the object is searched for the attribute of the given name.
    If the given object is not of type 'type', then the MRO of the type of the object is searched for the attribute.
    The return value distinguishes the following cases:
        0. The name was found and refers to a property. The term evaluates to the setter of that property.
        1. The name was found and refers to an instance variable. The term valuates to a NameReference.
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
            attr = (value if t.subtypeof(Type.instance) else t).resolve_member(self.name)

            if isinstance(attr, int):
                return FieldReference(value, attr)
            if isinstance(attr, VProperty):
                return attr.setter
            elif isinstance(attr, VProcedure):
                return VTypeError("Cannot assign values to method fields!")
            else:
                raise TypeError(type(attr))
        except KeyError:
            return VAttributeError()


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

    @property
    def components(self):
        """
        The terms that evaluate to the components of the tuple.
        :return:
        """
        return self.children

    def evaluate(self, tstate, mstate):
        return VTuple(*(c.evaluate(tstate, mstate) for c in self.components))


class NewList(Term):
    """
    A term that evaluates to a new empty list.
    """

    def __init__(self):
        """
        Creates a new list term.
        """
        super().__init__()

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

    @property
    def etype(self):
        """
        The subclass of VJumpException that is to be instantiated by this term.
        """
        return self._etype

    def evaluate(self, tstate, mstate):
        return self._etype()


class NewTypeError(Term):
    """
    A term that evaluates to a TypeError.
    """

    def __init__(self, message):
        """
        Creates a new tuple term.
        :param message: The message for the type error created by this term.
        """
        super().__init__()
        self._msg = check_type(message, str)

    @property
    def message(self):
        """
        The message for the type error created by this term.
        """
        return self._msg

    def evaluate(self, tstate, mstate):
        return VTypeError(self._msg)


class NewNamespace(Term):
    """
    A term that evaluates to a new empty namespace.
    """

    def __init__(self):
        """
        Creates a new namespace term.
        """
        super().__init__()

    def evaluate(self, tstate, mstate):
        return VNamespace()


class NewProcedure(Term):
    """
    A term that evaluates to a new VProcedure object.
    """

    def __init__(self, num_args, entry):
        """
        Creates a new procedure creation term.
        :param num_args: The number of arguments of the procedure to be created by this term.
        :param entry: The StackProgram or the ProgramLocation representing the code to be executed by the procedure created by this term.
        """
        super().__init__()
        self._num_args = check_type(num_args, int)
        self._entry = check_type(entry, (ProgramLocation, StackProgram))

    @property
    def num_args(self):
        """
        The number of arguments of the procedure to be created by this term.
        """
        return self._num_args

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
        return VProcedure(self._num_args, e)


class NumArgs(Term):
    """
    A term determining the number of arguments of a procedure.
    """

    def __init__(self, arg):
        """
        Creates a new NumArgs term.
        :param arg: The term representing the procedure object the number of arguments of which is to be determined.
        """
        super().__init__(arg)

    def evaluate(self, tstate, mstate):
        p = self.children[0].evaluate(tstate, mstate)
        return VInt(p.num_args)


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
        return VProperty(g, s)


class NewClass(Term):
    """
    A term that evaluates to a new Type object.
    """

    def __init__(self, superclasses, namespace):
        """
        Creates a new Class term.
        :param superclasses: An iterable of terms that evaluate to super classes
                             of the class to be created by this term.
        :param namespace: A term evaluating to a namespace binding names to members
                          of the class to be created by this term.
        """
        super().__init__(*superclasses, namespace)

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
        ns = self.namespace.evaluate(tstate, mstate)
        return TClass(ss, ns)


class NewModule(Term):
    """
    A term that evaluates to a new Module object.
    """

    def __init__(self, namespace):
        """
        Creates a new module term.
        :param namespace: A term evaluating to a namespace binding names to members
                          of the module to be created by this term.
        """
        super().__init__(namespace)

    @property
    def namespace(self):
        """
        A term evaluating to a namespace binding names to members of the module to be created by this term.
        """
        return self.children[0]

    def evaluate(self, tstate, mstate):
        ns = self.namespace.evaluate(tstate, mstate)
        return VModule(ns)

