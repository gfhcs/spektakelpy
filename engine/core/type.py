import abc

from engine.core.value import Value
from util import check_type, check_types


def linearization(t):
    """
    Computes the linearization ("mro") of the given type according to C3.
    :param t: The type the resolution of which is to be computed.
    :return: An iterable of super types of the given type.
    """

    # Python's C3 MRO, as documented in https://www.python.org/download/releases/2.3/mro/

    def merge(seqs):
        while True:
            nonempty = [seq for seq in seqs if len(seq) > 0]
            if len(nonempty) == 0:
                break
            cand = None
            for seq in nonempty:  # find merge candidates among seq heads
                cand = seq[0]
                nothead = [s for s in nonempty if any(cand.equals(other) for other in s[1:])]
                if nothead:
                    cand = None  # reject candidate
                else:
                    break
            if cand is None:
                raise ValueError("Inconsistent hierarchy!")
            yield cand
            for seq in nonempty:  # remove cand
                if seq[0].equals(cand):
                    seq.pop(0)

    return merge([[t], *(list(linearization(b)) for b in t.bases), list(t.bases)])


class Type(Value, abc.ABC):
    """
    A Type describes a set of abilities and an interface that a value provides.
    """

    def __init__(self, name, bases, direct_members):
        """
        Creates a new type.
        :param name: The name of this type.
        :param bases: A tuple of Type objects that the new type inherits from.
        :param direct_members: A mapping from names to Values that defines the *direct* members of this type.
        """
        super().__init__()
        self._name = check_type(name, str)
        self._bases = check_types(bases, Type)
        self._members_direct = {str(check_type(k, str)): check_type(v, Value) for k, v in direct_members.items()}
        self._mro = list(linearization(self))

    @property
    def name(self):
        """
        The name of this type.
        :return: A str.
        """
        return self._name

    @property
    def bases(self):
        """
        The base types inherited by this type.
        :return: An iterable of Type objects.
        """
        return self._bases

    @property
    def mro(self):
        """
        The method resolution order of this type, i.e. a linearization of the hierarchy of all its super types.
        :return: An iterable of Types.
        """
        return self._mro

    @property
    def direct_members(self):
        """
        A mapping from names to members that belong directly to this type (i.e. that are not inherited from other types).
        :return: A dict-like object.
        """
        return self._members_direct

    class MemberMap:
        def __init__(self, mro):
            self._mro = mro

        def __getitem__(self, name):
            for t in self._mro:
                try:
                    return t.direct_members[name]
                except KeyError:
                    continue
            raise KeyError(f"{self._mro[0]} has no attribute '{name}'!")

    @property
    def members(self):
        """
        A mapping from names to members that are part of this type (including inherited members).
        :return: A dict-like object.
        """
        return Type.MemberMap(self.mro)

    def hash(self):
        return len(self.direct_members)

    def equals(self, other):
        return self is other

    def bequals(self, other, bijection):
        try:
            return bijection[id(self)] == id(other)
        except KeyError:
            bijection[id(self)] = id(other)
            if not (isinstance(other, Type)
                    and (self._name, len(self._bases), len(self._members_direct))
                    == (other._name, len(other._bases), len(other._members_direct))):
                return False

            for name, member in self._members_direct.items():
                try:
                    member_other = other._members_direct[name]
                except KeyError:
                    return False

                if not member.bequals(member_other, bijection):
                    return False

            return all(a.bequals(b, bijection) for a, b in zip(self._bases, other._bases))

    def cequals(self, other):
        return self is other

    def chash(self):
        return hash(self._name) ^ hash(tuple(b.chash() for b in self._bases))

    def subtypeof(self, other):
        """
        Decides if this type is a subtype of another type, i.e. whether it is either equal to that type, or inherits
        from it.
        :param other: A Type object.
        :return: A bool.
        """

        if self.cequals(other):
            return True

        for s in self.bases:
            if s.subtypeof(other):
                return True

        return False

    def print(self, out):
        out.write(self._name)

    def _seal(self):
        for b in self.bases:
            b.seal()
        for m in self._members_direct.values():
            m.seal()

    @property
    @abc.abstractmethod
    def num_cargs(self):
        """
        The number of arguments expected by self.new .
        :return: Either an int, or None. If None is returned, the constructor ignores constructor arguments.
        """
        pass

    @abc.abstractmethod
    def new(self, *args):
        """
        Creates a new, uninitialized instance of this type.
        :param args: The constructor arguments for instance creation.
        :return: A Value object the type of which is this type.
        """
        pass
