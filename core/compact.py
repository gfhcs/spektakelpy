import abc


class CompactObject(abc.ABC):
    """
    An object that can represent a set of alternative values in a "compact", but possibly overapproximating way.
    """

    @abc.abstractmethod
    def equal(self, other):
        """
        Defines if this compact object is equal to a given compact object. If so, the objects may be used interchangeably,
        without the user being able to tell which object they are using.
        :param other: A compact object.
        :return: A boolean value.
        """
        pass

    @abc.abstractmethod
    def hash(self):
        """
        Computes a hash value for this object. If two compact objects are equal to each other, they must have the same
        hash value.
        :return: An int.
        """
        pass

    def __eq__(self, other):
        return self.equal(other)

    def __ne__(self, other):
        return not self.equal(other)

    def __hash__(self):
        return self.hash()
