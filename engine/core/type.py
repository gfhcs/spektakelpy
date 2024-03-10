from engine.core.value import Value
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
                raise ValueError("Inconsistent hierarchy!")
            yield cand
            for seq in nonempty:  # remove cand
                if seq[0] == cand:
                    seq.pop(0)

    return merge([[t], *(list(linearization(b)) for b in t.bases), list(t.bases)])


class Type(Value):
    """
    A Type describes a set of abilities and an interface that a value provides.
    """

    __instance_type = None
    __instance_object = None

    def __init__(self, name, super_types, field_names, members):
        """
        Creates a new type.
        :param name: A name for this type.
        :param super_types: The super types this type inherits from.
        :param field_names: An iterable of str objects specifying the instance field names of this type.
        :param members: A dict mapping str names to instance procedures and properties of this type.
        """
        super().__init__()
        self.seal()
        self._name = check_type(name, str)
        self._super_types = tuple(check_type(t, Type) for t in super_types)
        self._field_names = tuple(field_names)
        self._members = {check_type(k, str): check_type(v, Value) for k, v in members.items()}
        self._mro = list(linearization(self))
        self._nfields = len(self._field_names)

        for t in self.mro:
            self._nfields += t._nfields

    @staticmethod
    def get_instance_object():
        """
        Returns the Type object that represents the type 'object'. This procedure always returns the same object.
        :return: A Type.
        """
        if Type.__instance_object is None:
            Type.__instance_object = Type("object", [], [], {})
        return Type.__instance_object

    @staticmethod
    def get_instance_type():
        """
        Returns the Type object that represents the type 'type'. This procedure always returns the same object.
        :return: A Type.
        """
        if Type.__instance_type is None:
            Type.__instance_type = Type("type", [Type.get_instance_object()], [], {})
        return Type.__instance_type

    def print(self, out):
        out.write(self._name)

    @property
    def name(self):
        """
        The name of this type.
        """
        return self._name

    @property
    def bases(self):
        """
        The base types inherited by this type.
        :return: A tuple of Type objects.
        """
        return self._super_types

    @property
    def type(self):
        return Type.get_instance_type()

    def hash(self):
        return id(self)

    def equals(self, other):
        return self is other

    def bequals(self, other, bijection):
        if self is other:
            return True
        try:
            return bijection[id(self)] == id(other)
        except KeyError:
            bijection[id(self)] = id(other)
            if not (isinstance(other, Type)
                    and (self._name, len(self._super_types), len(self._field_names), len(self._members))
                    == (other._name, len(other._super_types), len(other._field_names), len(other._members))):
                return False
            if not (all(a == b for a, b in zip(self._field_names, other._field_names))
                    and all(a.bequals(b, bijection) for a, b in zip(self._super_types, other._super_types))):
                return False
            for k, v in self._members.items():
                try:
                    if not v.bequals(other._members[k]):
                        return False
                except KeyError:
                    return False
            return True

    def cequals(self, other):
        return self.equals(other)

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

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._field_names[key]
        else:
            return self._members[key]

    def resolve_member(self, name):
        """
        Retrieves the type member of the given name, by searching the entire method resolution order of this type.
        :param name: The name of the member to retrieve.
        :return: Either an integer representing an instance field, or a VProcedure object, or a VProperty object.
        :exception VAttributeError: If no member with the given name could be found.
        """

        foffset = 0
        for t in self.mro:
            try:
                fidx = t._field_names.index(name)
                return foffset + fidx
            except ValueError:
                try:
                    return t[name]
                except KeyError:
                    pass

            foffset += len(t._field_names)

        raise KeyError(f"{self} has no attribute '{name}'!")
