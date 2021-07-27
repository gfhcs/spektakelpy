import abc
from enum import Enum

from syntax.buffer import BufferedMatchStream
from syntax.lexical.pythonesque import TokenType


class LexErrorReason(Enum):
    """
    The reason for a lexer error.
    """
    INVALIDINPUT = 0  # The next characters in the input stream are not matched by any lexical rule.
    OUTOFTOKENS = 1  # No tokens are left in the input.
    UNEXPECTEDEOS = 2  # Unexpected end of input.
    UNEXPECTEDTOKEN = 3  # Unexpected token type.


class LexError(Exception):
    """
    An error that occured while lexing a string.
    """
    def __init__(self, reason, pos=None):
        """
        Instantiates a new LexError.
        :param reason: The reason for this error.
        """

        if reason == LexErrorReason.INVALIDINPUT:
            msg = "Cannot interpret the input as a token!"
        elif reason == LexErrorReason.OUTOFTOKENS:
            msg = "No tokens are left in the input stream!"
        elif reason == LexErrorReason.UNEXPECTEDEOS:
            msg = "Unexpected end of input!"
        elif reason == LexErrorReason.UNEXPECTEDTOKEN:
            msg = "Unexpected token!"
        else:
            raise NotImplementedError("No exception message has been defined for {}!".format(reason))

        if pos is not None:
            msg = "Line {}, column {}: ".format(pos.line, pos.column) + msg

        super().__init__(msg)

        self._reason = reason
        self._pos = pos

    @property
    def reason(self):
        """
        The reason for this error.
        :return: A LexErrorReason.
        """
        return self._reason

    @property
    def position(self):
        """
        The position in the lexer input stream at which this error occurred.
        :return: A TokenPosition object.
        """
        return self._pos


class LexicalGrammar(abc.ABC):
    """
    An instance of this class completely specifies the lexical grammar of a formal language.
    """

    @abc.abstractmethod
    def generate_tokens(self, buffer):
        """
        A generator for tokens lexed from a character stream.
        :param buffer: A BufferedMatchStream the contents of which will be tokenized.
        :return: A generator of triples (kind, text, position) that represent the tokens that were lexed.
        """
        pass


class Lexer:
    """
    A lexer makes a sequence of characters available as a sequence of tokens, to be processed by a parser.
    """

    def __init__(self, spec, source):
        """
        Creates a new lexer.
        :param spec: The LexicalGrammar used for lexing.
        :param source: A text stream providing input characters.
        """

        self._g = iter(spec.generate_tokens(BufferedMatchStream(source)))
        self._peek = None

    def peek(self):
        """
        Retrieves the token the lexer is currently seeing, without advancing to the next token.
        :return: A triple (t, s, p) consisting of TokenType t, token text s and token position p.
                 The final token in any error-free input is EOS. After this token has been consumed, this method
                 raises a LexError.
        """

        if self._peek is None:
            try:
                self._peek = next(self._g)
            except StopIteration:
                # This cannot happen, because we never *read* the END token.
                raise

        return self._peek

    def read(self):
        """
        Retrieves the token the lexer is currently seeing, and advances to the next token.
        :exception LexError: If the token to be read is of type END.
        :return: A tuple as returned by Lexer.peek.
        """
        t, s, p = self.peek()
        if t == TokenType.END:
            raise LexError(LexErrorReason.OUTOFTOKENS, pos=p)
        self._peek = None
        return t, s, p

    def match(self, p):
        """
        Asserts that the token the lexer is currently seeing satisfies the given predicate, retrieves it and
        advances to the next token.
        :param p: The predicate to be satisfied by the token to be retrieved.
        :exception LexError: If the lexer is not seeing a satisfying token.
        :return: A tuple as returned by Lexer.peek.
        """
        t, s, p = self.peek()
        if not p(t):
            raise LexError(LexErrorReason.UNEXPECTEDTOKEN, p)
        return self.read()

    def seeing(self, p):
        """
        Decides if the current token the lexer is facing satisfies the given predicate.
        The token is not consumed.
        :param p: The predicate to be satisfied.
        :exception LexError: If the lexer is not seeing a valid token.
        :return: A boolean value.
        """
        return p(self.peek())


def expected(s=None, t=None):
    """
    Constructs a predicate asserting that a given token has the specified type and text.
    :param t: The expected TokenType.
    :param s: The expected text of the token.
    :return: A predicate procedure.
    """
    def p(f):
        ft, fs, _ = f
        return (t is None or ft == t) and (s is None or fs == s)

    return p


def end():
    """
    Constructs a predicate asserting that a given token is the END token.
    :return: A predicate procedure.
    """
    return expected(t=TokenType.END)


def keyword(s=None):
    """
    Constructs a predicate asserting that a given token is the expected keyword.
    :param s: The expected text of the token.
    :return: A predicate procedure.
    """
    return expected(t=TokenType.KEYWORD, s=s)


def identifier(s=None):
    """
    Constructs a predicate asserting that a given token is an identifier.
    :param s: The expected text of the token.
    :return: A predicate procedure.
    """
    return expected(t=TokenType.IDENTIFIER, s=s)


def literal():
    """
    Constructs a predicate asserting that a given token is a literal.
    :return: A predicate procedure.
    """
    return expected(t=TokenType.LITERAL)
