import abc

from engine.functional.values import Value
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

    def __init__(self, name, *super_types):
        """
        Creates a new type.
        :param name: A name for this type.
        :param super_types: The super types this type inherits from.
        """
        super().__init__()
        self._name = check_type(name, str)
        self._super_types = tuple(check_type(t, Type) for t in super_types)
        self._mro = linearization(self)

    @property
    def type(self):
        return TBuiltin.type

    def hash(self):
        return hash(id(self))

    def equals(self, other):
        return id(self) == id(other)

    def _seal(self):
        pass

    def clone_unsealed(self, cloned=None):
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

    @abc.abstracmethod
    def resolve_direct_member(self, name, instance):
        """
        Looks up a *direct* type member, ignoring any base classes.
        :param name: The name of the member to retrieve.
        :param instance: The Value object for which to retrieve the member.
        :return: Either a Reference object, or a Procedure object.
        """
        pass

    def resolve_member(self, name, instance, direct):
        """
        Retrieves the type member of the given name, by searching the entire method resolution order of this type.
        :param name: The name of the member to retrieve.
        :param instance: The Value object for which to retrieve the member.
        :return: Either a Reference object, or a Procedure object.
        """
        if not instance.type.subtypeof(self):
            raise ValueError("The given instance is not a member of this type!")
        for t in self.mro:
            try:
                return t.resolve_direct_member(name, instance, True)
            except ValueError:
                continue
        raise ValueError("No type in the MRO of {} could resolve a member named '{}'!".format(self, name))

    @abc.abstractmethod
    def create_instance(self):
        """
        Creates an instance of this type.
        :return: An instance of this type. The __init__ method must be called immediately after creation of the object.
        """
        pass





class TBuiltin(Type):
    # TODO: All builtin types should be instances of this type.
    # Built-in data types should be the same as for python: bool, int, float, str, tuple, list, dict, object, type, exception, task, function, module
    pass

class TException(Type):
    pass


TException.instance = TException()


class TFunction(Type):
    pass


TFunction.instance = TFunction()

class TStopIteration:
    pass

TStopIteration.instance = TStopIteration()

class TClass(Type):
    pass