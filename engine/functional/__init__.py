import abc
from abc import ABC

from engine.functional.types import builtin_type, TBuiltin
from engine.functional.values import VAttributeError, VProperty, VProcedure, VInstance
from engine.intrinsic import IntrinsicProcedure
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
        Decides if for every machine state m containing self, there exists a bijection between the object identities in
        m and the object identities in some machine state m', such that self is mapped to other and
        bijection(m).equals(m').

        This procedure is thus more permissive than self.equals. It must be compatible with self.hash, i.e.
        for all bijections b self.bequals(other, b) must imply self.hash() == other.hash().

        This procedure is used to decide if two MachineState objects of different Python identity are actually representing
        indistinguishable Spek machine states: For this comparison, absolute Python object identities do not matter,
        but *equality* of Python object identities within the same state does.

        In contrast, self.equals must decide if a machine program can possibly tell self apart from other, which may
        often be the case based on type or Python object identity! While self.equals implements == and != *in Python*,
        self.cequals implements them in Spek, where they may be more permissive (for example for comparing integers
        to booleans).

        :param other: Another Value.
        :param bijection: A mapping from ID's s of Values to ID's e of Values, that this procedure may only *extend*,
                  without modifying pre-existing key-value pairs.
                  If bijection[id(s)] = id(e), the sub-value s of self is considered indistinguishable
                  from the sub-value e of other.
                  The mapping must not contain Values that are only distinguishable by content, because in that case,
                  multiple Value objects of different identity can be indistinguishable, which cannot be represented
                  in a bijection.
                  The mapping must contain all sub values of self and other that are distinguishable by identity.
        :return: A boolean value.
        """
        pass

    @abc.abstractmethod
    def cequals(self, other):
        """
        Implements the == and != operators in Spek. It may be more permissive than self.equals: self.equals must
        not be True for value pairs that a machine program could tell apart in anyway, including object identity or
        type. However, according to the Spek semantics, values for which self.equals returns False might still be
        considered equal by ==, for example because they are convertible into each other, as is the case for integers
        and some floats.

        This procedure must be compatible with self.hash,
        i.e. self.cequals(other) must imply self.hash() == other.hash().

        :param other: Another Value.
        :return: A boolean value.
        """
        pass


@builtin_type("reference", [TBuiltin.object])
class Reference(Value, abc.ABC):
    """
    A reference is a part of a machine state that can point to another part of a machine state.
    """

    def type(self):
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
        :exception VException: If evaluation fails for a semantic reason.
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


@builtin_type("type", [TBuiltin.object])
class Type(Value, ABC):
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
        self.seal()
        self._name = check_type(name, str)
        self._super_types = tuple(check_type(t, Type) for t in super_types)
        self._field_names = tuple(field_names)
        self._members = {check_type(k, str): check_type(v, (VProperty, VProcedure, IntrinsicProcedure)) for k, v in members.items()}
        self._mro = list(linearization(self))
        self._nfields = len(self._field_names)

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
        return TBuiltin.type

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
                    return t._members[name]
                except KeyError:
                    pass

            foffset += len(t._field_names)

        raise VAttributeError(f"{self} has no attribute '{name}'!")

    def create_instance(self):
        """
        Creates an instance of this type.
        :return: An instance of this type. The __init__ method must be called immediately after creation of the object.
        """
        return VInstance(self, self._nfields)