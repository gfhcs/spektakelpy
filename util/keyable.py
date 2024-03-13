from weakref import WeakValueDictionary

from util.immutable import Immutable


# Note: We chose not to offer a 'Countable' type, because mapping instances to integers is similar to what Keyable
#       is doing and we believe that lookup in the WeakValueDictionary is at least as performant as binary search
#       over a sorted list of weak references.

class Keyable(Immutable):
    """
    A type the instances of which can bijectively mapped to hashable keys.
    """

    instances = None

    def __new__(cls, key, *largs, **kwargs):
        if cls.instances is None:
            cls.instances = WeakValueDictionary()
        try:
            return cls.instances[key]
        except KeyError:
            value = super().__new__(cls, *largs, **kwargs)
            cls.instances[key] = value
            return value

    def __init__(self, key, *largs, **kwargs):
        """
        :param key: A hashable object that uniquely identifies this instance.
        :param largs: Further constructor arguments, to be passed on.
        :param kwargs: Further constructor arguments, to be passed on.
        """
        super().__init__(*largs, **kwargs)
        self._key = key

    @property
    def instance_key(self):
        """
        A hashable object that uniquely identifies this instance.
        """
        return self._key

    def hash(self):
        return hash(self._key)

    def equals(self, other):
        return isinstance(other, type(self)) and self._key == other._key
