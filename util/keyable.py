from weakref import WeakValueDictionary

from util.immutable import Immutable


# Note: We chose not to offer a 'Countable' type, because mapping instances to integers is similar to what Keyable
#       is doing and we believe that lookup in the WeakValueDictionary is at least as performant as binary search
#       over a sorted list of weak references.

class Keyable(Immutable):
    """
    A type the instances of which can bijectively mapped to hashable keys.
    """

    key2instance = None
    # hits = 0

    def __new__(cls, key, *largs, **kwargs):
        if cls.key2instance is None:
            cls.key2instance = WeakValueDictionary()
        try:
            return cls.key2instance[key]
        except KeyError:
            instance = super().__new__(cls, *largs, **kwargs)
            instance._key = key
            cls.key2instance[key] = instance
            # cls.hits -= 1
            return instance
        finally:
            # cls.hits += 1
            # print(f"{cls.hits} hits on {len(cls.key2instance)} instances.")
            pass

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
