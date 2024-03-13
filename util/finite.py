from util.immutable import Immutable


class Finite(Immutable):
    """
    A type with a sufficiently small, finite number of possible instances.
    """

    index2instance = None

    def __new__(cls, index, *largs, **kwargs):
        index = int(index)
        if cls.index2instance is None:
            cls.index2instance = [None, ] * (index + 1)
        elif index >= len(cls.index2instance):
            cls.index2instance.extend([None, ] * (index + 1 - len(cls.index2instance)))
        instance = cls.index2instance[index]
        if instance is None:
            instance = super().__new__(cls, *largs, **kwargs)
            instance._iindex = index
            cls.index2instance[index] = instance
        return instance

    @property
    def instance_index(self):
        """
        A nonnegative integer that uniquely identifies this instance.
        """
        return self._iindex

    def hash(self):
        return self._iindex

    def equals(self, other):
        return isinstance(other, type(self)) and self._iindex == other._iindex
