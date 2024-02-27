import abc

from util import check_type
from util.immutable import Sealable, Immutable
from util.printable import Printable


class Value(Sealable, Printable, abc.ABC):
    """
    Represents a runtime value.
    """

    @property
    @abc.abstractmethod
    def type(self):
        """
        The type that this value belongs to.
        :return: A Type object.
        """
        pass

    @abc.abstractmethod
    def bequals(self, other, bijection):
        """
        Decides whether a machine program could tell this value apart from another value.
        This method must be compatible with self.hash, i.e. if this method returns True, we must have
        self.hash() == other.hash().
        This procedure is used to compare machine states to one another: We must be able to tell whether two objects
        representing machine states are actually representing the *same* machine state, even though their Python
        identities are truly different. This is why a bijection from sub-value references in one object to sub-value
        references in the other object needs to be built up. Only in that way can we decide equality of Values that
        the machine could tell apart by their identities.
        :param other: Another Value.
        :param bijection: A mapping from ID's s of Values to ID's e of Values.
                  If bijection[id(s)] = id(e), the sub-value s of self is considered indistinguishable
                  from the sub-value e of other.
                  The mapping must not contain Values that are only distinguishable by content, because in that case,
                  multiple Value objects of different identity can be indistinguishable, which cannot be represented
                  in a bijection.
                  The mapping must contain all sub values of self and other that are distinguishable by identity.
                  self.bequals must *extend* the mapping accordingly, i.e. it may only *add* keys.
        :return: A boolean value indicating if any machine program could distinguish self from other.
        """
        pass

    def equals(self, other):
        return self.bequals(other, {})


class Reference(Value, abc.ABC):
    """
    A reference is a part of a machine state that can point to another part of a machine state.
    """

    def type(self):
        from engine.functional.types import TBuiltin
        return TBuiltin.ref

    @abc.abstractmethod
    def write(self, tstate, mstate, value):
        """
        Updates the value stored at the location that this reference is pointing to.
        :param tstate: The TaskState in the context of which this reference is to be interpreted. It must be part
                       of the given mstate.
        :param mstate: The MachineState in the context of which this reference is to be interpreted. It must contain
                       tstate.
        :param value: The value to store at the location that this reference is pointing to.
        """
        pass

    @abc.abstractmethod
    def read(self, tstate, mstate):
        """
        Obtains the value that this reference is pointing to.
        :param tstate: The TaskState in the context of which this reference is to be interpreted. It must be part
                       of the given mstate.
        :param mstate: The MachineState in the context of which this reference is to be interpreted. It must contain
                       tstate.
        :return: The object pointed to by this reference.
        """
        pass


class EvaluationException(Exception):
    """
    Raised when the evaluation of a term fails.
    """
    pass


class Term(Immutable, Printable, abc.ABC):
    """
    A term is a type of expression that is evaluated atomically and functionally, meaning that intermediate states
    of its evaluation are not semantically observable and that evaluation cannot change the machine state ever.
    Even when evaluation should fail, an error is merely reported as an exception.

    Terms can be seen as a special type of machine instruction: Instead of making the instruction set of our virtual
    machine rather large, to support all the different ways in which computations can be combined, we keep the set of
    proper instructions quite small and use terms whenever possible. Terms are beneficial mostly because they do not
    change the machine state and thus can be evaluated safely without unforeseen side effects.
    """

    def __init__(self, *children):
        super().__init__()
        for c in children:
            check_type(c, Term)
        self._children = children

    def __ne(self, other):
        return not self.__eq__(other)

    @abc.abstractmethod
    def evaluate(self, tstate, mstate):
        """
        Evaluates this expression in the given state.
        :param tstate: The task state that this expression is to be evaluated in. It must be part of the given machine
        state. Any references to task-local variables will be interpreted with respect to this task state.
        :param mstate: The machine state that this expression is to be evaluated in. It must contain the given task
        state.
        :exception EvaluationException: If evaluation fails for a semantic reason.
        :return: An object representing the value that evaluation resulted in.
        """
        pass

    @property
    def children(self):
        """
        The children of this term.
        """
        return self._children


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
        from engine.functional.values import VProperty, VProcedure
        from engine.intrinsic import IntrinsicProcedure

        super().__init__()
        self._name = check_type(name, str)
        self._super_types = tuple(check_type(t, Type) for t in super_types)
        self._field_names = field_names
        self._members = {check_type(k, str): check_type(v, (VProperty, VProcedure, IntrinsicProcedure)) for k, v in members.items()}
        self._mro = list(linearization(self))
        self._nfields = len(field_names)

        for t in self.mro:
            self._nfields += t._nfields

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
        from engine.functional.types import TBuiltin
        return TBuiltin.type

    def hash(self):
        return id(self)

    def equals(self, other):
        return self is other

    def bequals(self, other, bijection):
        return self is other

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
            try:
                fidx = t._field_names.index(name)
                return foffset + fidx
            except ValueError:
                try:
                    return t._members[name]
                except KeyError:
                    pass

            foffset += len(t._field_names)

        raise AttributeError(f"{self} has no attribute '{name}'!")

    def create_instance(self):
        """
        Creates an instance of this type.
        :return: An instance of this type. The __init__ method must be called immediately after creation of the object.
        """
        from .values import VInstance
        return VInstance(self, self._nfields)