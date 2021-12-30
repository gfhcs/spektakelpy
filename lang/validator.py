from lang.spek.ast import *


class ValidationError(Exception):
    """
    A failure to validate an AST node.
    """

    def __init__(self, msg, node, mspec):
        """
        Instantiates a new ValidationError.
        :param msg: The message for this error.
        :param node: The node to which the error belongs.
        :param mspec: The ModuleSpecification for the module the validation failure occured in.
        """

        check_type(node, Node)
        msg = "Line {}, column {}: ".format(node.start.line + 1, node.start.column + 1) + msg

        super().__init__(msg)
        self._node = node
        self._mspec = mspec

    @property
    def node(self):
        """
        The node at which this error occured.
        :return: A Node object.
        """
        return self._node

    @property
    def mspec(self):
        """
        The ModuleSpecification for the module the validation error occured in.
        """
        return self._mspec


class Validator(abc.ABC):
    """
    A validator computes static properties of an AST.
    """

    @abc.abstractmethod
    def validate(self, node, env=None, mspec=None):
        """
        Validates an AST node.
        :param node: The AST node to validate.
        :param env: An Environment, mapping names to definitions.
        :param mspec: The ModuleSpecification specifying the AST that contains the given 'node'.
        :return: A pair (env2, dec, err), where env2 is an Environment, dec is a dict mapping AST nodes to decorations
                 and err is an iterable of ValidationError objects.
        """
        pass


