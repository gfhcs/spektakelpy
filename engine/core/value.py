import abc

from util.immutable import Sealable
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
        Analogously, this procedure must be compatible with self.chash.

        :param other: Another Value.
        :return: A boolean value.
        """
        pass

    @abc.abstractmethod
    def chash(self):
        """
        Returns a hash value for this value. If self.cequals(other), then self.chash() == other.chash()
        :return: An int.
        """
        pass
