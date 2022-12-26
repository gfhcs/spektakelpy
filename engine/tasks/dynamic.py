import abc
from util.immutable import Immutable
# TODO: Here we should have data structures that exist at runtime, such as Function, Type. A function should
# contain a CFG as the representation of its body.


class Namespace(Immutable):
    """
    An immutable object that represents a mapping from names to values.
    """

    def __init__(self):
        """
        Creates the empty namespace.
        """

    def adjoin(self, name, value):
        """
        Computes a new namespace object, that maps the given name to the given value and otherwise behaves like
        the current namespace. The method does not modify the current namespace.
        :param name: A string.
        :param value: A runtime object that the name is to be mapped to.
        :return: A namespace object.
        """
        pass

    def delete(self, name):
        """
        Computes a new namespace object, that does not contain the given name and otherwise behaves like
        the current namespace. The method does not modify the current namespace.
        :param name: A string.
        :return: A namespace object.
        """
        pass

    def lookup(self, name):
        """
        Looks up the given name in this name space.
        :param name: The name to look up.
        :return: The runtime object that was retrieved.

        """
        pass
