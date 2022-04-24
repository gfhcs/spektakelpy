import abc


class Finder(abc.ABC):
    """
    A finder maps syntactic module names to module specifications.
    """

    @abc.abstractmethod
    def find(self, name, validator=None):
        """
        Finds a module for the given name.
        :param name: A name pointing to a module, usually an AST node.
        :param validator: The Validator calling this method (if any).
        :return: A ModuleSpecification object.
        :exception KeyError: If no module could be found for the given name.
        """
        pass


class AdjoinedFinder(Finder):
    """
    Represents the adjunction of two finders, i.e. all names not resolved by one finder will be resolved by the other
    one.
    """

    def __init__(self, f, g):
        """
        Adjoins one finder with another.
        :param f: The finder that is to be tried when the other one does not find the requested name.
        :param g: The finder that is to be tried first.
        """
        super().__init__()
        self._f = f
        self._g = g

    def find(self, name, validator=None):
        try:
            return self._g.find(name, validator=validator)
        except KeyError:
            return self._f.find(name, validator=validator)


class ModuleSpecification(abc.ABC):
    """
    A module specification describes a module that is to be loaded (*before* it is loaded).
    """

    @abc.abstractmethod
    def load(self, *largs, **kwargs):
        """
        Loads the module specified by this object.
        :return: A Module object.
        """
        pass


class Module(abc.ABC):
    """
    A module maps a number of names to their definitions.
    """

    @property
    @abc.abstractmethod
    def errors(self):
        """
        An iterable of ValidationError objects that occured in this module.
        """
        pass

    @property
    @abc.abstractmethod
    def names(self):
        """
        The names defined in this module.
        :return: An iterable of strings.
        """
        pass

    @abc.abstractmethod
    def resolve(self, name):
        """
        Maps a name defined in this module to its definition.
        :param name: A string.
        :return: The definition retrieved for the given name.
        :exception KeyError: If this module does not contain a definition for the given name.
        """
        pass

    def __contains__(self, name):
        try:
            self.resolve(name)
        except KeyError:
            return False

    def __len__(self):
        return len(self.names)

    def __iter__(self):
        for n in self.names:
            yield n, self.resolve(n)

    def __getitem__(self, name):
        return self.resolve(name)
