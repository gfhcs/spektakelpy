from engine.core.data import VNone, VInt, VFloat, VStr, VBool
from engine.core.exceptions import VException, VCancellationError, VRuntimeError
from engine.core.intrinsic import intrinsic
from engine.core.machine import TaskState
from engine.core.procedure import Procedure
from engine.core.type import Type
from engine.core.value import Value
from engine.stack.exceptions import VReferenceError, VTypeError, VInstructionException
from util import check_type

__collected = {}


def builtin(name=None):
    """
    Decorates intrinsic types and procedures as globally visible in Spek.
    This decorator can be used on Python types decorated with @intrinsic or @intrinsic_type,
    and on Python procedures decorated with @intrinsic or @intrinsic_procedure.
    This decorator does not modify its argument, but registers it in the collection of built-in values.
    :param name: The name under which the type or procedure should be visible.
    """

    def decorate(x):
        nonlocal name

        if isinstance(x, (Procedure, Type)):
            y = x
        elif callable(x) and not isinstance(x, type):
            raise TypeError("The @builtin decorator only works on Python functions that are decorated with "
                            "@intrinsic or @intrinsic_procedure!")
        elif isinstance(x, type):
            try:
                y = x.machine_type
            except AttributeError:
                raise TypeError("The @builtin decorator only works on Python types that have a 'machine_type' "
                                "attribute, such as those decorated with @intrinsic or @intrinsic_type!")
            assert isinstance(y, Type)
        else:
            raise TypeError("The @builtin decorator only works on procedures and types!")

        if name is None:
            try:
                name = y.name
            except AttributeError:
                try:
                    name = y.__name__
                except AttributeError:
                    raise ValueError("No name for the builtin value was given and none could be inferred!")

        if name in __collected:
            raise ValueError(f"There already is a Value registered under the name '{name}'!")
        __collected[name] = check_type(y, Value)

        return x

    return decorate


def all_builtin():
    """
    Enumerates all builtin values.
    :return: An iterable of pairs (name, value), where name is the string name under which the Value value should
             be visible globally in Spek.
    """
    return iter(__collected.items())


builtin()(Type.get_instance_object())
builtin()(Type.get_instance_type())
builtin()(Procedure.machine_type)
builtin()(VNone.machine_type)
builtin()(VBool.machine_type)
builtin()(VInt.machine_type)
builtin()(VFloat.machine_type)
builtin()(VStr.machine_type)
builtin()(VException.machine_type)
builtin()(VCancellationError.machine_type)
builtin()(VRuntimeError.machine_type)
builtin()(TaskState.machine_type)
builtin()(VReferenceError.machine_type)
builtin()(VTypeError.machine_type)
builtin()(VInstructionException.machine_type)


@builtin("isinstance")
@intrinsic()
def builtin_isinstance(x, types):
    if not isinstance(types, tuple):
        types = (types, )
    t = x.type
    return VBool.from_bool(any(t.subtypeof(s) for s in types))
