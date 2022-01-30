import abc


class ImmutableEquatable:
    """
    An object that is both immutable and defines an abstract equality.
    """

    @abc.abstractmethod
    def hash(self):
        """
        Computes a hash value for this object.
        This method must be compatible with self.equals.
        """
        pass

    @abc.abstractmethod
    def equals(self, other):
        """
        Decides whether this object is considered equal to another object.
        This method must be compatible with self.hash
        :param other: An object.
        :return: A boolean value.
        """
        pass

    def __hash__(self):
        return self.hash()

    def __eq__(self, other):
        return self.equals(other)

    def __ne__(self, other):
        return not self.equals(other)
