from enum import Enum
from inspect import signature

from engine.core.atomic import AtomicType
from engine.core.compound import VCompound
from engine.core.procedure import Procedure
from engine.core.property import OrdinaryProperty
from engine.core.type import Type
from engine.core.value import Value
from util import check_types, check_type


class IntrinsicProcedure(Procedure):
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

    def _seal(self):
        return self

    def hash(self):
        return hash(self._p)

    def equals(self, other):
        return self is other or isinstance(other, IntrinsicProcedure) and self._p is other._p

    def bequals(self, other, bijection):
        return self.equals(other)

    def cequals(self, other):
        return self.equals(other)

    def clone_unsealed(self, clones=None):
        return self

    def print(self, out):
        out.write(f"IntrinsicProcedure({self._p})")

    def initiate(self, tstate, mstate, *args):
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
            if isinstance(instance, VCompound):
                instance = instance[instance.type.get_offset(itype)]
            if not isinstance(instance, ptype):
                raise TypeError(f"The type of the given instance is not derived from the Python type {ptype}!")
            return method(instance, *args)

        super().__init__(operate)


class IntrinsicInit(IntrinsicProcedure):
    """
    Wraps a Python constructor as an intrinsic procedure that initializes an instance of an intrinsic type.
    """
    def __init__(self, ptype, itype, construct):
        """
        Wraps a Python instance method.
        :param ptype: The Python type that should be wrapped by the instances treated by this intrinsic initializer.
        :param itype: The intrinsic type that is to contain this initializer as a direct member.
        :param construct: A Python class method that returns Value objects of a Python type that is given as its first
                       argument.
        """
        def init(instance, *args):
            if isinstance(instance, VCompound):
                instance[instance.type.get_offset(itype)] = construct(ptype, *args)
            else:
                if not isinstance(instance, ptype):
                    raise TypeError(f"The type of the given instance is not derived from the Python type {ptype}!")
                # The instance is already initialized.

        super().__init__(init)
        self._construct = construct

    @property
    def construct(self):
        """
        The Python class method that constructs the instances wrapped by the intrinsic type this intrinsic initializer
        belongs to.
        :return: A Python procedure that takes a Python type derived from Value as its first argument and returns
                 an object of that type.
        """
        return self._construct


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

        try:
            ptype.intrinsic_type
        except AttributeError:
            pass
        else:
            raise ValueError(f"The Python type {ptype} has already been wrapped as an intrinsic type!")

        check_type(name, str)
        check_type(ptype, type)
        if not issubclass(ptype, Value):
            raise TypeError("In order for a class to be wrapped as an intrinsic type, it must be a subclass of Value!")
        check_types(bases, Type)

        for s in bases:
            if not isinstance(s, Type):
                raise ValueError(f"Some of the super types of {ptype} are not proper Type objects!")

        members = {}
        new = None

        # If there is an initializer in the MRO of ptype, we want to inherit it:
        for base in ptype.mro():
            if base is ptype:
                continue
            try:
                base_intrinsic = base.intrinsic_type
                assert isinstance(base_intrinsic, IntrinsicType)
            except AttributeError:
                continue
            try:
                init = base_intrinsic.direct_members["__init__"]
                assert isinstance(init, IntrinsicInit)
                members["__init__"] = IntrinsicInit(ptype, self, init.construct)

                def new(*args):
                    return init.construct(ptype, *args)
            except KeyError:
                continue
            break

        for iname, pname in pmembers.items():

            pmember = getattr(ptype, pname)

            if iname == "__init__":
                if pname == "__init__":
                    def construct(cls, *args):
                        return cls(*args)
                else:
                    construct = pmember
                imember = IntrinsicInit(ptype, self, construct)

                def new(*args):
                    return construct(ptype, *args)

            elif isinstance(pmember, property):
                getter = IntrinsicInstanceMethod(ptype, self, pmember.fget)
                setter = None if pmember.fset is None else IntrinsicInstanceMethod(ptype, self, pmember.fset)
                imember = OrdinaryProperty(getter, setter)
            else:
                imember = IntrinsicInstanceMethod(ptype, self, pmember)

            members[iname] = imember

        super().__init__(name, bases, new=new, members=members)


# While a decorated Python type is under construction, this maps from intrinsic member names to Python member names:
__intrinsic_collection__ = {}

class CollectionType(Enum):
    GLOBAL = 0
    GENERIC = 1
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
            if name is None:
                name = x.__name__
            __intrinsic_collection__[name] = x.__name
            return x
        finally:
            collection_stack.pop()

    return decorator


def intrinsic_init():
    """
    Decorates a class method of a Python type, to be turned into an instance constructor.
    """

    if tuple(collection_stack[1:]) not in ((CollectionType.TYPE, ),):
        raise TypeError("@intrinsic_member may only be used for members of Python types that "
                        "are themselves decorated with @intrinsic_type!")
    collection_stack.append(CollectionType.INIT)

    def decorator(x):
        try:
            __intrinsic_collection__["__init__"] = x.__name__
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

            IntrinsicType(name, t, bases, __intrinsic_collection__)

            return t
        finally:
            collection_stack.pop()

    return decorator
