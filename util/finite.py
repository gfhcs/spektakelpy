from util.immutable import Immutable


class Finite(Immutable):
    """
    A type with a sufficiently small, finite number of possible instances.
    """

    instances = []

    def __new__(cls, index, *largs, **kwargs):
        index = int(index)
        if index >= len(cls.instances):
            cls.instances.extend([None, ] * (index + 1 - len(cls.instances)))
        instance = cls.instances[index]
        if instance is None:
            instance = super().__new__(cls, *largs, **kwargs)
            cls.instances[index] = instance
        return instance

    def __init__(self, iindex, *largs, **kwargs):
        """
        :param iindex: A nonnegative integer determining the identity of the instance to create.
        :param largs: Further constructor arguments, to be passed on.
        :param kwargs: Further constructor arguments, to be passed on.
        """
        super().__init__(*largs, **kwargs)
        self._iindex = iindex

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
