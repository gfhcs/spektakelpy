import abc

from util import check_type
from util.immutable import Sealable


class Value(Sealable, abc.ABC):
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


class Term(abc.ABC):
    """
    Defines the types and semantics of expressions that the virtual machine can evaluate.
    A term is an expression the evaluation of which happens atomically and cannot cause any side effects.
    This means that evaluation is not observable and that evaluating a term can in no way change the machine state.
    """

    def __init__(self, *children):
        super().__init__()
        for c in children:
            check_type(c, Term)
        self._children = children

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
        from .values import VInstance
        return VInstance(self, self._nfields)