import abc


class UnsealedException(RuntimeError):
    """
    An exception that occurs when an object would have to be immutable, but is still mutable.
    """
    pass


class SealedException(RuntimeError):
    """
    An exception that occurs when an object would have to be mutable, but is actually immutable.
    """
    pass


def check_sealed(sealable):
    """
    Raises an UnsealedException if the given object is unsealed.
    :param sealable: A Sealable object.
    :exception UnsealedException: If the given object is unsealed.
    :return: The given sealable.
    """
    if not sealable.sealed:
        raise UnsealedException("The object is mutable, but would have to be sealed for this operation!")
    return sealable


def check_unsealed(sealable):
    """
    Raises a SealedException if the given object is sealed.
    :param sealable: A Sealable object.
    :exception UnsealedException: If the given object is sealed.
    :return: The given sealable.
    """
    if sealable.sealed:
        raise SealedException("The object is sealed, but would have to be mutable for this operation!")
    return sealable


class Sealable:
    """
    An object that is mutable after its construction, but can be sealed, to become immutable.
    """

    def __init__(self):
        super().__init__()
        self._sealed = False

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

    @abc.abstractmethod
    def _seal(self):
        """
        Makes this object immutable.
        self.hash must raise a SealException before this method has been called.
        Any other methods that would modify the state of the object must raise a SealException *after* this method
        has been called.
        """
        pass

    def seal(self):
        """
        Seals this object, i.e. makes it immutable.
        """
        if not self._sealed:
            self._seal()
            self._sealed = True

    @property
    def sealed(self):
        """
        Indicates if this object has been sealed and is thus guaranteed to not ever be modified again.
        """
        return self._sealed

    @abc.abstractmethod
    def clone_unsealed(self):
        """
        Creates a deep copy of this object, that is unsealed and equal to this object.
        """
        pass


class Immutable(Sealable, abc.ABC):
    """
    An object that is both immutable and defines an abstract equality.
    """

    def __init__(self):
        super().__init__()
        self._sealed = True

    def _seal(self):
        pass

    def clone_unsealed(self):
        return self
