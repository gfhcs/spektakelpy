from engine.functional import Type
from engine.functional.values import VInstance, VBool, VInt, VFloat, VStr, VTuple, VList, VDict, \
    VException, VTypeError, VJumpError, VReturnError, VBreakError
from engine.intrinsic import IntrinsicInstanceMethod


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
            members = {}

        for n in dir(ptype):
            member = getattr(ptype, n)
            if isinstance(member, IntrinsicInstanceMethod):
                members[n] = member

        super().__init__(name, super_types, [], members)
        self._ptype = ptype

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


TBuiltin.object = TBuiltin("object", [], VInstance)
TBuiltin.type = TBuiltin("type", [TBuiltin.object], None)
TBuiltin.ref = TBuiltin("reference", [TBuiltin.object], None)
TBuiltin.bool = TBuiltin("bool", [TBuiltin.object], VBool)
TBuiltin.int = TBuiltin("int", [TBuiltin.object], VInt)
TBuiltin.float = TBuiltin("float", [TBuiltin.object], VFloat)
TBuiltin.str = TBuiltin("str", [TBuiltin.object], VStr)
TBuiltin.tuple = TBuiltin("tuple", [TBuiltin.object], VTuple)
TBuiltin.list = TBuiltin("list", [TBuiltin.object], VList)
TBuiltin.dict = TBuiltin("dict", [TBuiltin.object], VDict,)
TBuiltin.exception = TBuiltin("exception", [TBuiltin.object], VException)
TBuiltin.jump_error = TBuiltin("JumpError", [TBuiltin.exception], VJumpError)
TBuiltin.return_error = TBuiltin("ReturnError", [TBuiltin.jump_error], VReturnError)
TBuiltin.break_error = TBuiltin("BreakError", [TBuiltin.jump_error], VBreakError)
TBuiltin.type_error = TBuiltin("TypeError", [TBuiltin.exception], VTypeError)
TBuiltin.procedure = TBuiltin("procedure", [TBuiltin.object], None)
TBuiltin.namespace = TBuiltin("namespace", [TBuiltin.object], None)
TBuiltin.module = TBuiltin("module", [TBuiltin.object], None)
TBuiltin.task = TBuiltin("task", [TBuiltin.object], None)
TBuiltin.location = TBuiltin("location", [TBuiltin.object], None)
