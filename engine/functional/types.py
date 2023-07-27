from engine.intrinsic import IntrinsicInstanceMethod
from engine.functional.values import Value, VInstance, VBool, VInt, VFloat, VStr, VTuple, VList, VDict, \
    VException
from util import check_type


def linearization(t):
    """
    Computes the linearization ("mro") of the given type according to C3.
    :param t: The type the resolution of which is to be computed.
    :return: An iterable of super types of the given type.
    """

    # Python's C3 MRO, as documented in https://www.python.org/download/releases/2.3/mro/

    def merge(seqs):
        i = 0
        while True:
            nonempty = [seq for seq in seqs if len(seq) > 0]
            if len(nonempty) == 0:
                break
            i += 1
            cand = None
            for seq in nonempty:  # find merge candidates among seq heads
                cand = seq[0]
                nothead = [s for s in nonempty if cand in s[1:]]
                if nothead:
                    cand = None  # reject candidate
                else:
                    break
            if cand is None:
                raise ValueError("Inconsistent hiearchy!")
            yield cand
            for seq in nonempty:  # remove cand
                if seq[0] == cand:
                    seq.pop(0)

    return merge([[t], *(list(linearization(b)) for b in t.bases), list(t.bases)])


class Type(Value):
    """
    A Type describes a set of abilities and an interface that a value provides.
    """

    def __init__(self, name, super_types, field_names, members):
        """
        Creates a new type.
        :param name: A name for this type.
        :param super_types: The super types this type inherits from.
        :param field_names: An iterable of str objects specifying the instance field names of this type.
        :param members: A dict mapping str names to instance procedures and properties of this type.

        """
        super().__init__()
        self._name = check_type(name, str)
        self._super_types = tuple(check_type(t, Type) for t in super_types)
        self._field_names = field_names
        self._members = members
        self._mro = linearization(self)
        self._nfields = len(field_names)

        for t in self.mro:
            self._nfields += t._nfields

    @property
    def bases(self):
        """
        The base types inherited by this type.
        :return: A tuple of Type objects.
        """
        return self._super_types

    @property
    def type(self):
        return TBuiltin.type

    def hash(self):
        return hash(id(self))

    def equals(self, other):
        return id(self) == id(other)

    def _seal(self):
        pass

    def clone_unsealed(self, clones=None):
        return self

    def subtypeof(self, other):
        """
        Decides if this type is a subtype of another type, i.e. whether it is either equal to that type, or inherits
        from it.
        :param other: A Type object.
        :return: A bool.
        """

        if self == other:
            return True

        for s in self._super_types:
            if s.subtypeof(other):
                return True

        return False

    @property
    def mro(self):
        """
        The method resolution order of this type, i.e. a linearization of the hierarchy of all its super types.
        :return: An iterable of Types.
        """
        return self._mro

    def resolve_member(self, name):
        """
        Retrieves the type member of the given name, by searching the entire method resolution order of this type.
        :param name: The name of the member to retrieve.
        :return: Either an integer representing an instance field, or a VProcedure object, or a VProperty object.
        """

        foffset = 0
        for t in self.mro:
            fidx = t._field_names.find(name)
            if fidx >= 0:
                return foffset + fidx
            try:
                return t._members[name]
            except KeyError:
                pass

            foffset += len(t._field_names)

    def create_instance(self):
        """
        Creates an instance of this type.
        :return: An instance of this type. The __init__ method must be called immediately after creation of the object.
        """
        return VInstance(self, self._nfields)


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

        for name in dir(ptype):
            member = getattr(ptype, name)
            if isinstance(member, IntrinsicInstanceMethod):
                members[name] = member

        super().__init__(name, super_types, [], members)
        self._ptype = ptype

    def create_instance(self):
        return self._ptype()


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
TBuiltin.procedure = TBuiltin("procedure", [TBuiltin.object], None)
TBuiltin.module = TBuiltin("module", [TBuiltin.object], None)
TBuiltin.task = TBuiltin("task", [TBuiltin.object], None)
