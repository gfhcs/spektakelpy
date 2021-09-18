
class Environment:
    """
    An immutable mapping of keys to values, that supports adjunction.
    """

    def __init__(self, k2v=None, base=None):
        """
        Creates a new environment, possibly by adjunction of an existing environemnt.
        :param base: The environment to adjoin.
        :param k2v: A dict-like object that maps keys in which the new environment should differ from the base to new values.
        """
        self._base = base
        self._k2v = {} if k2v is None else dict(k2v)
        self._len = len(self._k2v)
        if base is not None:
            self._len += len(base)

    def __len__(self):
        return self._len

    def __iter__(self):
        for k, v in self._k2v.items():
            yield k, v

        for k, v in self._base:
            if k not in self._k2v:
                yield k, v

    def __getitem__(self, key):
        try:
            return self._k2v[key]
        except KeyError:
            if self._base is None:
                raise
            return self._base[key]

    def adjoin(self, k2v):
        """
        Adjoins this environment, i.e. creates a new environment that agrees with this one, except in the given
        keys.
        This method does not modify this environment!
        :param k2v: A dict-like object that maps keys in which the new environment should differ from this one to new values.
        :return: A new Environment.
        """
        return Environment(k2v, self)
