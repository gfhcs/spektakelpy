import abc
from abc import ABC
from inspect import signature

from engine.core.type import Type
from engine.core.value import Value
from engine.core.property import Property
from engine.core.procedure import Procedure
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

    def __call__(self, *args):
        return self._p(*args)


class IntrinsicMember(Value, ABC):
    """
    A Value that is a member of a Python class, and to be visible in the Spek version of that class.
    """

    @property
    @abc.abstractmethod
    def member_name(self):
        """
        The name that this member should have in Spek, regardless of its name in Python.
        :return: A str object.
        """
        pass


class IntrinsicMethod(IntrinsicProcedure, IntrinsicMember):
    """
    A method of a Python class that can also be used as an intrinsic procedure at runtime.
    """

    def __init__(self, name, method):
        """
        Creates a new intrinsic method.
        :param name: The name under which this method should be visible in Spek.
        :param method: The method to wrap.
        """
        super().__init__(method)
        self._name = check_type(name, str)
        self.__isabstractmethod__ = getattr(method, '__isabstractmethod__', False)

    @property
    def member_name(self):
        return self._name

    def equals(self, other):
        return super().equals(other) and self._name == other._name

    def bequals(self, other, bijection):
        return super().bequals(other, bijection) and self._name == other._name

    def cequals(self, other):
        return super().equals(other) and self._name == other._name


class IntrinsicConstructor(IntrinsicMethod):
    """
    Represents the intrinsic constructor of a Python type.
    """

    def __init__(self, t=None, m=None):
        """
        Builds a constructor that can be used to create instances of the given in type in both Python and Spek.
        :param t: The Python type instances of which are to be constructed. If None is given, calling the intrinsic
                  constructor will raise a ValueError.
        :param m: Either a class method, or an __init__ method. Either will be used to construct instances in this
                  constructor.
        """

        self._m = m

        if isinstance(m, classmethod):
            c = m.__func__
        elif m.__name__ == "__init__" and next(iter(signature(m).parameters)) == "self":
            def c(t, *largs, **kwargs):
                return t(*largs, **kwargs)
        else:
            raise TypeError("IntrinsicConstructor only accepts class methods and  __init__ procedures!")

        if t is None:
            def construct(*_, **__):
                raise TypeError("This intrinsic constructor has not been given a Python type "
                                "and can therefor not actually construct any instances!")
        else:
            def construct(*largs, **kwargs):
                return c(t, *largs, **kwargs)

        super().__init__("__new__", construct)
        self._m = m
        self._t = t

    @property
    def python_type(self):
        """
        The Python type that this constructor creates *direct* instances of.
        :return: Either a type object, or None, if no type was given.
        """
        return self._t

    @property
    def method(self):
        """
        The original Python method that this intrinsic constructor was made of.
        """
        return self._m

    def __call__(self, *args, **kwargs):
        return self._m(*args, **kwargs)


class IntrinsicProperty(property, Property, IntrinsicMember):
    """
    A property of a Python class that can also be used as an instance property at runtime.
    """

    def __init__(self, name, getter, setter=None):
        """
        Creates a new intrinsic instance property.
        :param name: The name under which this property should be visible in Spek.
        :param getter: The Python getter to wrap.
        :param setter: The Python setter to wrap.
        """
        super().__init__(getter, setter)
        super(property, self).__init__()
        self._name = name
        self._igetter = IntrinsicMethod(f"{name}_igetter", getter)
        self._isetter = None if setter is None else IntrinsicMethod(f"{name}_isetter", setter)

    @property
    def member_name(self):
        return self._name

    @property
    def getter_procedure(self):
        return self._igetter

    @property
    def setter_procedure(self):
        return self._isetter

    def print(self, out):
        out.write("IntrinsicProperty(")
        self.getter_procedure.print(out)
        if self.setter_procedure is not None:
            out.write(", ")
            self.setter_procedure.print(out)
        out.write(")")

    def intrinsic_setter(self, setter):
        """
        Turns this property into one that has a setter. This method is meant to be used as a setter decorator,
        exactly like with the 'setter' attribute of ordinary Python properties.
        :param setter: The setter to be added to this property.
        :return: An IntrinsicProperty object.
        """
        return IntrinsicProperty(self._name, self.fget, setter)

    def hash(self):
        return id(self)

    def equals(self, other):
        return self is other

    def bequals(self, other, bijection):
        return self is other

    def cequals(self, other):
        return self is other

    def _seal(self):
        self._igetter.seal()
        self._isetter.seal()

    def clone_unsealed(self, clones=None):
        return self


def intrinsic_procedure():
    """
    Turns a Python procedure into a Procedure object.
    :return: A Procedure object.
    """
    return lambda p: IntrinsicProcedure(p)


def intrinsic_method(name=None):
    """
    Turns an instance method of a Python class into an IntrinsicMethod.
    :param name: The name under which the method should be visible in Spek.
    :return: An IntrinsicMethod object.
    """
    def decorator(x):
        nonlocal name
        if name is None:
            name = x.__name__
        return IntrinsicMethod(name, x)
    return decorator


def intrinsic_property(name=None):
    """
    Wraps a Python instance method as an IntrinsicProperty, which is also a Python property.
    :param name: The name under which the property should be visible in Spek.
    :return: An IntrinsicProperty object.
    """
    def decorator(x):
        nonlocal name
        if name is None:
            name = x.__name__
        return IntrinsicProperty(name, x)
    return decorator


def intrinsic_constructor():
    """
    Turns a class method of a Python class into an IntrinsicMethod that can be used as a constructor in Spek.
    :param construct: The static method to turn into a constructor.
    :return: An IntrinsicMethod.
    """

    def decorator(construct):
        # We expect the Type constructor to fill in the proper Python type once it has been constructed.
        return IntrinsicConstructor(t=None, m=construct)

    return decorator


def intrinsic_type(name=None, super_types=None):
    """
    Turns a Python class definition into a Type that can be used in Spek.
    :return: A Type object.
    """

    def decorator(t):
        nonlocal name, super_types

        if not isinstance(t, type):
            raise TypeError("The 'builtin_type' decorator only works on classes!")

        if not issubclass(t, Value):
            raise TypeError("In order for a class to be turned into a Spek type, it must be a subclass of Value!")

        if name is None:
            name = t.__name__

        if super_types is None:
            super_types = tuple(b.machine_type for b in t.__bases__ if hasattr(b, "machine_type"))

        for s in super_types:
            if not isinstance(s, Type):
                raise ValueError(f"Some of the super types of {t.__name__} are not proper Type objects!")

        members = {}

        # If there is a constructor in the MRO of the super types, we want to inherit it:
        for s in t.mro():
            try:
                s_intrinsic = s.machine_type
            except AttributeError:
                continue
            try:
                members["__new__"] = s_intrinsic["__new__"]
            except KeyError:
                continue
            break

        for n in dir(t):
            member = getattr(t, n)
            if not isinstance(member, IntrinsicMember):
                continue
            members[member.member_name] = member

        # If there is a constructor, it is expected to be an IntrinsicConstructor.
        # It is coming either from a super class, or was defined in the decorated type.
        # In both cases we must fill in the decorated type as the type to construct:
        try:
            constructor = members["__new__"]
        except KeyError:
            pass
        else:
            assert isinstance(constructor, IntrinsicConstructor)
            members["__new__"] = IntrinsicConstructor(t=t, m=constructor.method)

        t.machine_type = Type(name, super_types, [], members).seal()
        return t

    return decorator


def intrinsic(*largs, **kwargs):
    """
    Decorates a Python procedure, method, or class as a Value object visible in Spek.
    :param largs: Arguments to be supplied to other intrinsic_* decorators.
    :param kwargs: Arguments to be supplied to other intrinsic_* decorators.
    """

    def decorator(x):
        if isinstance(x, type):
            return intrinsic_type(*largs, **kwargs)(x)
        else:
            s = signature(x)
            if next(iter(s.parameters.values())).name == "self":
                if x.__name__ == "__init__":
                    return intrinsic_constructor(*largs, **kwargs)(x)
                else:
                    return intrinsic_method(*largs, **kwargs)(x)
            elif isinstance(x, property):
                raise TypeError("Do not use @property and @intrinsic together! Instead use @intrinsic_property!")
            elif isinstance(x, classmethod):
                raise NotImplementedError("Cannot mark class methods as intrinsic!")
            elif isinstance(x, staticmethod):
                raise NotImplementedError("Cannot mark static methods as intrinsic!")
            else:
                return intrinsic_procedure(*largs, **kwargs)(x)

    return decorator
