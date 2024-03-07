from engine.functional import Type, Value
from engine.functional.values import IntrinsicProperty
from engine.intrinsic import IntrinsicInstanceMethod, IntrinsicConstructor


class TBuiltin(Type):
    """
    Represents a builtin type, i.e. one the user did not define via a class declaration.
    """

    def __init__(self, name, super_types, ptype):
        """
        Creates a new type.
        :param name: A name for this type.
        :param super_types: The super types this type inherits from.
        :param ptype: The Python type that represents instances of this type. It must be a callable that yields
                      instances when given no arguments at all.
        :param members: A dict mapping str names to instance procedures and properties of this type. It will be extended
                        by those members of ptype that were decorated with @intrinsic.instancemethod.
        """

        members = {}
        for n in dir(ptype):
            member = getattr(ptype, n)
            if isinstance(member, (IntrinsicInstanceMethod, IntrinsicProperty)):
                members[n] = member
            elif isinstance(member, IntrinsicConstructor):
                members["__new__"] = member
            else:
                continue

        super().__init__(name, super_types, [], members)
        self._ptype = ptype

        self.seal()

    @classmethod
    @property
    def instances(cls):
        """
        Enumerates all the instances of builtin types that have been declared as attributes of TBuiltin.
        """
        for name in dir(cls):
            attribute = getattr(TBuiltin, name)
            if isinstance(attribute, TBuiltin):
                yield attribute


def builtin_type(name=None, super_types=None):
    """
    Turns a Python type into type that is built into Spek.
    :param name:
    :param super_types:
    :return:
    """
    def decorator(t):
        nonlocal name, super_types

        if not isinstance(t, type):
            raise TypeError("The 'builtin_type' decorator only works on classes!")

        if not issubclass(t, Value):
            raise TypeError("In order for a class to be turned into a Spek type, it must be a subclass of Value!")

        if name is None:
            name = t.__name__
            if name[0] != "V":
                raise ValueError("By convention the names of Value subtypes that correspond to Spek types should start with 'V'!")
            name = name[1:].lower()

        if super_types is None:
            super_types = tuple(t.__bases__)

        for s in super_types:
            if not isinstance(s, Type):
                raise ValueError(f"Some of the super types of {t.__name__} are not proper Type objects!")

        if hasattr(TBuiltin, name):
            raise ValueError("TBuiltin already has a member of name '{name}'!")

        setattr(TBuiltin, name, TBuiltin(name, super_types, t))

        return t

    return decorator
