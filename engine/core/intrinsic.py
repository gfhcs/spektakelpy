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

    @property
    def num_args(self):
        """
        The number of arguments of this procedure.
        """
        return len(signature(self._p).parameters)

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


def intrinsic_init():
    """
    Turns the __init__ method of a Python class into an IntrinsicMethod that can be used as a constructor in Spek.
    :param init: The __init__ method to turn into a constructor.
    :return: An IntrinsicMethod.
    """
    return lambda init: IntrinsicMethod("__init__", init)


def intrinsic_constructor():
    """
    Turns a static method of a Python class into an IntrinsicMethod that can be used as a constructor in Spek.
    :param construct: The static method to turn into a constructor.
    :return: An IntrinsicMethod.
    """
    return lambda construct: IntrinsicMethod("__new__", construct)


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
        for n in dir(t):
            member = getattr(t, n)
            if not isinstance(member, IntrinsicMember):
                continue

            mname = member.member_name

            if mname == "__new__":
                if "__new__" in members:
                    raise ValueError(f"There seem to be multiple intrinsic constructors for {t}!")
            elif member.member_name == "__init__":
                mname = "__new__"
                member = IntrinsicMethod(mname, t)
            else:
                pass

            members[mname] = member

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
                    return intrinsic_init(*largs, **kwargs)(x)
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
