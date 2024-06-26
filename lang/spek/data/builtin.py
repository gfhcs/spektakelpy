from engine.core.atomic import type_object, type_type
from engine.core.none import type_none
from engine.core.data import VInt, VFloat, VStr, VBool, VIndexError, VException, VCancellationError, VRuntimeError, \
    VKeyError, VIterator, VStopIteration
from engine.core.intrinsic import intrinsic_procedure, intrinsic_type, intrinsic_member
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
    This decorator can be used on Python types decorated with @intrinsic_type,
    and on Python procedures decorated with @intrinsic_procedure.
    This decorator does not modify its argument, but registers it in the collection of built-in values.
    :param name: The name under which the type or procedure should be visible.
    """

    def decorate(x):
        nonlocal name

        if isinstance(x, (Procedure, Type)):
            y = x
        elif callable(x) and not isinstance(x, type):
            raise TypeError("The @builtin decorator only works on Python functions that are decorated with "
                            "@intrinsic_procedure!")
        elif isinstance(x, type):
            try:
                y = x.intrinsic_type
            except AttributeError:
                raise TypeError("The @builtin decorator only works on Python types that have a 'intrinsic_type' "
                                "attribute, such as those decorated with @intrinsic_type!")
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

# TaskState needs to be made intrinsic first, which we did not do in the core package because that would
# lead to "conceptual circular imports":
it = intrinsic_type("task", [type_object])
intrinsic_member()(TaskState.cancel)
it(TaskState)
del it


builtin()(type_object)
builtin()(type_type)
builtin()(Procedure.intrinsic_type)
builtin()(type_none)
builtin()(VBool.intrinsic_type)
builtin()(VInt.intrinsic_type)
builtin()(VFloat.intrinsic_type)
builtin()(VStr.intrinsic_type)
builtin()(VException.intrinsic_type)
builtin()(VCancellationError.intrinsic_type)
builtin()(VRuntimeError.intrinsic_type)
builtin()(TaskState.intrinsic_type)
builtin()(VReferenceError.intrinsic_type)
builtin()(VTypeError.intrinsic_type)
builtin()(VInstructionException.intrinsic_type)
builtin()(VIndexError.intrinsic_type)
builtin()(VKeyError.intrinsic_type)
builtin()(VStopIteration.intrinsic_type)


@builtin("isinstance")
@intrinsic_procedure()
def builtin_isinstance(x, types):
    if not isinstance(types, tuple):
        types = (types, )
    t = x.type
    return VBool(any(t.subtypeof(s) for s in types))


@builtin("len")
@intrinsic_procedure()
def builtin_len(x):
    return VInt(len(x))

@builtin("iter")
@intrinsic_procedure()
def builtin_iter(iterable):
    try:
        i = iter(iterable)
        if not isinstance(i, VIterator):
            raise TypeError()
        return i
    except TypeError:
        raise VTypeError(f"'{iterable.type}' is not iterable!")


@builtin("next")
@intrinsic_procedure()
def builtin_next(iterator):
    if not isinstance(iterator, VIterator):
        raise VTypeError(f"'{iterator.type}' object is not an iterator")
    return iterator.next()
