from enum import Enum
from inspect import signature, Parameter

from engine.core.atomic import AtomicType
from engine.core.compound import VCompound, as_atomic
from engine.core.procedure import Procedure
from engine.core.property import OrdinaryProperty
from engine.core.type import Type
from engine.core.value import Value
from util import check_types, check_type
from util.immutable import Immutable


class IntrinsicProcedure(Immutable, Procedure):
    """
    A procedure the execution of which is not observable, i.e. the procedure is executed atomically, without giving
    access to intermediate machine states.
    """

    def __init__(self, p):
        """
        Turns a Python procedure into an intrinsic Spek procedure.
        :param p: The Python procedure to turn into Procedure object.
        """
        if not hasattr(p, "__call__"):
            raise TypeError("The given procedure must be a callable!")
        super().__init__()
        self._p = p

    def hash(self):
        return hash(self._p)

    def equals(self, other):
        return self is other or isinstance(other, IntrinsicProcedure) and self._p is other._p

    def bequals(self, other, bijection):
        return self.equals(other)

    def cequals(self, other):
        return self.equals(other)

    def chash(self):
        return self.hash()

    def print(self, out):
        out.write(f"IntrinsicProcedure({self._p})")

    def initiate(self, tstate, mstate, *args):
        return self._p(*check_types(args, Value))

    def __call__(self, *args):
        return self._p(*check_types(args, Value))


class IntrinsicInstanceMethod(IntrinsicProcedure):
    """
    Wraps a Python instance method as an intrinsic procedure that can operate on instances of an intrinsic type.
    """
    def __init__(self, ptype, itype, method):
        """
        Wraps a Python instance method.
        :param ptype: The Python type that this instance method belongs to.
        :param itype: The intrinsic type that is to contain this instance method as a direct member.
        :param method: A Python instance method. It accepts a Value as the first argument.
        """
        def operate(instance, *args):
            instance = as_atomic(instance, itype)
            if not isinstance(instance, ptype):
                raise TypeError(f"The type of the given instance is not derived from the Python type {ptype}!")
            return method(instance, *args)

        super().__init__(operate)


class IntrinsicProperty(Immutable, OrdinaryProperty):
    """
    Wraps a Python property. Like all intrinsic type members, this one must be immutable, in order to be compatible
    with AtomicType.
    """
    def __init__(self, ptype, itype, p):
        """
        Wraps a Python property.
        :param ptype: The Python type the property is derived from.
        :param itype: The intrinsic type that is to contain this property as a direct member.
        :param p: A property object.
        """
        getter = IntrinsicInstanceMethod(ptype, itype, p.fget)
        setter = None if p.fset is None else IntrinsicInstanceMethod(ptype, itype, p.fset)

        super().__init__(getter, setter)


class IntrinsicType(AtomicType):
    """
    Wraps a Python type as an intrinsic type, i.e. as a type that can be used as part of the machine state.
    """

    def __init__(self, name, ptype, bases, pmembers):
        """
        Wraps a Python type as an intrinsic type.
        :param name: The name of the new type. May deviate from the name of the Python type.
        :param ptype: The Python type to wrap. Must be a subtype of Value.
        :param bases: An iterable of the *intrinsic* base types.
        :param pmembers: A mapping from intrinsic member names to Python member names. All Python members contained in
                         this mapping will be turned into members of the intrinsic type.
        """

        self._ptype = ptype

        check_type(name, str)
        check_type(ptype, type)
        if not issubclass(ptype, Value):
            raise TypeError("In order for a class to be wrapped as an intrinsic type, it must be a subclass of Value!")
        check_types(bases, Type)

        for s in bases:
            if not isinstance(s, Type):
                raise ValueError(f"Some of the super types of {ptype} are not proper Type objects!")

        members = {}
        num_cargs = 0

        # In case we are inheriting the constructor of a base type, record its number of arguments:
        for base in ptype.mro():
            if base is ptype:
                continue
            try:
                base_intrinsic = base.intrinsic_type
            except AttributeError:
                continue
            assert isinstance(base_intrinsic, IntrinsicType)
            if "__init__" in base_intrinsic.direct_members:
                num_cargs = base_intrinsic.num_cargs
                break

        for iname, pname in pmembers.items():

            pmember = getattr(ptype, pname)

            if iname == "__init__":
                num_cargs = sum(1 for p in signature(pmember).parameters.values() if p.kind == Parameter.POSITIONAL_OR_KEYWORD) - 1

            if isinstance(pmember, property):
                imember = IntrinsicProperty(ptype, self, pmember)
            else:
                imember = IntrinsicInstanceMethod(ptype, self, pmember)

            members[iname] = imember

        def new(*args):
            return ptype.__new__(ptype, *args)

        super().__init__(name, bases, new=new, num_cargs=num_cargs, members=members)

    @property
    def python_type(self):
        """
        The Python type modelled by this intrinsic type.
        :return: A type object.
        """
        return self._ptype

    def clone_unsealed(self, clones=None):
        return self


# While a decorated Python type is under construction, this maps from intrinsic member names to Python member names:
__intrinsic_collection__ = {}


class CollectionType(Enum):
    GLOBAL = 0
    TYPE = 2
    PROCEDURE = 3
    MEMBER = 4
    INIT = 5


collection_stack = [CollectionType.GLOBAL]


def intrinsic_procedure():
    """
    Turns a Python procedure into a Procedure object.
    :return: A Procedure object.
    """

    if tuple(collection_stack[1:]) not in ((),):
        raise TypeError("@intrinsic_procedure may only be used on the module level!")
    collection_stack.append(CollectionType.PROCEDURE)

    def decorate(x):
        try:
            return IntrinsicProcedure(x)
        finally:
            collection_stack.pop()

    return decorate


def intrinsic_member(name=None):
    """
    Decorates a member of a Python type, to be turned into a member of the resulting intrinsic type.
    :param name: The name under which the method should be visible in Spek.
    """
    if tuple(collection_stack[1:]) not in ((CollectionType.TYPE, ),):
        raise TypeError("@intrinsic_member may only be used for members of Python types that "
                        "are themselves decorated with @intrinsic_type!")
    collection_stack.append(CollectionType.MEMBER)

    def decorator(x):
        nonlocal name
        try:
            pname = x.fget.__name__ if isinstance(x, property) else x.__name__
            if name is None:
                name = pname
            __intrinsic_collection__[name] = pname
            return x
        finally:
            collection_stack.pop()

    return decorator


def intrinsic_type(name=None, bases=None):
    """
    Turns a Python class definition into a Type that can be used in Spek.
    :return: A Type object.
    """

    if tuple(collection_stack[1:]) not in ((),):
        raise TypeError("@intrinsic_type may only be used on the module level!")
    collection_stack.append(CollectionType.TYPE)

    def decorator(t):
        nonlocal name, bases
        try:
            if name is None:
                name = t.__name__

            if bases is None:
                bases = tuple(b.intrinsic_type for b in t.__bases__ if hasattr(b, "intrinsic_type"))

            try:
                t.intrinsic_type
            except AttributeError:
                pass
            else:
                if t.intrinsic_type.python_type is t:
                    raise ValueError(f"The Python type {t} has already been wrapped as an intrinsic type!")

            t.intrinsic_type = IntrinsicType(name, t, bases, __intrinsic_collection__)

            return t
        finally:
            __intrinsic_collection__.clear()
            collection_stack.pop()

    return decorator
