from inspect import signature, Parameter

from engine.functional import Type, Reference
from engine.functional.values import VInstance, VBool, VInt, VFloat, VStr, VTuple, VList, VDict, \
    VException, VTypeError, VJumpError, VReturnError, VBreakError, VCell, VFuture, VProcedure, VNamespace, VFutureError, \
    IntrinsicProperty, VNone, VAttributeError
from engine.intrinsic import IntrinsicInstanceMethod, IntrinsicProcedure


class BuiltinConstructor(IntrinsicProcedure):
    """
    An __init__ method of a Python class that can be used to create instances at runtime.
    """

    def __init__(self, ptype):
        super().__init__()
        self._ptype = ptype
        s = signature(ptype.__init__)
        self._num_args = sum(1 for n, p in s.parameters.items() if n != "self" and p.kind == Parameter.POSITIONAL_ONLY)

    @property
    def num_args(self):
        return self._num_args

    def print(self, out):
        out.write("BuiltinConstructor(")
        out.write(str(self._ptype))
        out.write(")")

    def execute(self, _, __, *args):
        return self._ptype(*args)

    def hash(self):
        return hash(self._ptype)

    def bequals(self, other, bijection):
        return isinstance(other, BuiltinConstructor) and self._ptype is other._ptype


class TBuiltin(Type):
    """
    Represents a builtin type, i.e. one the user did not define via a class declaration.
    """

    def __init__(self, name, super_types, ptype, members=None):
        """
        Creates a new type.
        :param name: A name for this type.
        :param super_types: The super types this type inherits from.
        :param ptype: The Python type that represents instances of this type. It must be a callable that yields
                      instances when given no arguments at all.
        :param members: A dict mapping str names to instance procedures and properties of this type. It will be extended
                        by those members of ptype that were decorated with @intrinsic.instancemethod.
        """

        if members is None:
            members = dict()
            members["__new__"] = BuiltinConstructor(ptype)

        for n in dir(ptype):
            member = getattr(ptype, n)
            if isinstance(member, (IntrinsicInstanceMethod, IntrinsicProperty)):
                members[n] = member

        super().__init__(name, super_types, [], members)
        self._ptype = ptype

        self.seal()

    def create_instance(self):
        return self._ptype()

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


from engine.task import TaskState
from engine.tasks.program import ProgramLocation

TBuiltin.object = TBuiltin("object", [], VInstance)
TBuiltin.none = TBuiltin("none", [TBuiltin.object], VNone)
TBuiltin.type = TBuiltin("type", [TBuiltin.object], Type)
TBuiltin.cell = TBuiltin("cell", [TBuiltin.object], VCell)
TBuiltin.future = TBuiltin("future", [TBuiltin.object], VFuture)
TBuiltin.ref = TBuiltin("reference", [TBuiltin.object], Reference)
TBuiltin.bool = TBuiltin("bool", [TBuiltin.object], VBool)
TBuiltin.int = TBuiltin("int", [TBuiltin.object], VInt)
TBuiltin.float = TBuiltin("float", [TBuiltin.object], VFloat)
TBuiltin.str = TBuiltin("str", [TBuiltin.object], VStr)
TBuiltin.tuple = TBuiltin("tuple", [TBuiltin.object], VTuple)
TBuiltin.list = TBuiltin("list", [TBuiltin.object], VList)
TBuiltin.dict = TBuiltin("dict", [TBuiltin.object], VDict,)
TBuiltin.exception = TBuiltin("Exception", [TBuiltin.object], VException)
TBuiltin.jump_error = TBuiltin("JumpError", [TBuiltin.exception], VJumpError)
TBuiltin.cancellation = TBuiltin("CancellationError", [TBuiltin.exception], VException)
TBuiltin.return_error = TBuiltin("ReturnError", [TBuiltin.jump_error], VReturnError)
TBuiltin.break_error = TBuiltin("BreakError", [TBuiltin.jump_error], VBreakError)
TBuiltin.type_error = TBuiltin("TypeError", [TBuiltin.exception], VTypeError)
TBuiltin.future_error = TBuiltin("FutureError", [TBuiltin.exception], VFutureError)
TBuiltin.attribute_error = TBuiltin("AttributeError", [TBuiltin.exception], VAttributeError)
TBuiltin.procedure = TBuiltin("procedure", [TBuiltin.object], VProcedure)
TBuiltin.namespace = TBuiltin("namespace", [TBuiltin.object], VNamespace)
TBuiltin.task = TBuiltin("task", [TBuiltin.object], TaskState)
TBuiltin.location = TBuiltin("location", [TBuiltin.object], ProgramLocation)
