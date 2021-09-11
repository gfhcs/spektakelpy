from syntax.phrasal.ast import *


class ValidationError(Exception):
    """
    A failure to validate an AST node.
    """

    def __init__(self, msg, node):
        """
        Instantiates a new ValidationError.
        :param msg: The message for this error.
        :param node: The node to which the error belongs.
        """

        check_type(node, Node)
        msg = "Line {}, column {}: ".format(node.start.line + 1, node.start.column + 1) + msg

        super().__init__(msg)
        self._node = node

    @property
    def node(self):
        """
        The node at which this error occured.
        :return: A Node object.
        """
        return self._node


class Validator(abc.ABC):
    """
    A validator computes static properties of an AST.
    """

    @classmethod
    @abc.abstractmethod
    def validate(cls, node, env):
        """
        Validates an AST node.
        :param node: The AST node to validate.
        :param env: An Environment, mapping names to definitions.
        :return: A pair (e, d), where e is an Environment and d is dict mapping AST nodes to decorations.
        """
        pass


