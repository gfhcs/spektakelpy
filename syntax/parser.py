from .ast import *


class ParserError(Exception):
    """
    A failure to parse a token stream.
    """

    def __init__(self, msg, pos=None):
        """
        Instantiates a new LexError.
        :param msg: The message for this error.
        :param pos: The position in the input stream at which this error was encountered.
        """

        if pos is not None:
            msg = "Line {}, column {}: ".format(pos.line, pos.column) + msg

        super().__init__(msg)
        self._pos = pos

    @property
    def position(self):
        """
        The position in the lexer input stream at which this error occurred.
        :return: A TokenPosition object.
        """
        return self._pos


class Parser(abc.ABC):
    """
    A parser turns sequences of tokens into abstract syntax trees.
    """

    @classmethod
    @abc.abstractmethod
    def parse_expression(cls, lexer):
        """
        Parses the AST of an expression.
        :param lexer: The lexer to consume tokens from.
        :return: An expression object.
        """
        pass

    @classmethod
    @abc.abstractmethod
    def parse_process(cls, lexer):
        """
        Parses the AST of a process.
        :param lexer: The lexer to consume tokens from.
        :return: A Statement object.
        """
        pass


