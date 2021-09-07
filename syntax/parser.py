from syntax.phrasal.ast import *


class ParserError(Exception):
    """
    A failure to parse a token stream.
    """

    def __init__(self, msg, pos=None):
        """
        Instantiates a new ParserError.
        :param msg: The message for this error.
        :param pos: The position in the input stream at which this error was encountered.
        """

        if pos is not None:
            check_type(pos, TokenPosition)
            msg = "Line {}, column {}: ".format(pos.line + 1, pos.column + 1) + msg

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
    def parse_block(cls, lexer):
        """
        Parses the AST of a block statement.
        :param lexer: The lexer to consume tokens from.
        :return: A Statement object.
        """
        pass


