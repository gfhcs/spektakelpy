import io
import re
from enum import Enum

from util import check_type


class LexErrorReason(Enum):
    """
    The reason for a lexer error.
    """
    UNKNOWN = 0  # No exact reason for the error has been determined.
    OUTOFTOKENS = 1  # No tokens are left in the input.


class LexError(Exception):
    """
    An error that occured while lexing a string.
    """
    def __init__(self, reason):
        """
        Instantiates a new LexError.
        :param reason: The reason for this error.
        """

        msg = "Unknown"

        super().__init__(msg)

        self._reason = reason

    @property
    def reason(self):
        return self._reason


class TokenType(Enum):
    """
    Describes types of syntactic tokens.
    """
    COMMENT = 0
    IDENTIFIER = 1
    KEYWORD = 2
    LITERAL = 3
    WHITESPACE = 4
    EOS = 5


class LexerSpecification:
    """
    An instance of this type completely determines a lexical grammar.
    """

    def __init__(self, keywords, separators, skip_whitespace=True, skip_comments=True):
        """
        Creates a new lexer specification.
        :param keywords: The strings that are to be lexed as keyword tokens.
                         They must contain only alphanumeric characters and the underscore and they
                         must not start with a digit.
        :param separators: The strings that are to be lexed as separators. Separators have the same token type
                           as keywords, but unlike keywords they cannot be substrings of identifier or keyword tokens.
        :param skip_whitespace: Specifies if the lexer should omit white space in its output (True, default),
                                or enumerate it (False).
        :param skip_comments: Specifies if the lexer should omit comments in its output (True, default),
                              or enumerate them (False).
        """
        super().__init__()

        # This code is loosely based on https://docs.python.org/3/library/re.html ("Writing a Tokenizer")

        pattern_identifier = r'(?!\D)\w+'

        # All keywords should be accepted by the identifier rule:
        automaton_identifier = re.compile(pattern_identifier)
        for kw in keywords:
            if re.fullmatch(automaton_identifier, kw) is None:
                raise ValueError("The keyword '{}' is illegal!".format(kw))
        pattern_keyword = '|'.join(re.escape(kw) for kw in reversed(sorted(keywords, key=len)))

        # In order to keep things simple we do not allow the alphabet for separators to intersect with the alphabet
        # for keywords or identifiers. Also there must not be any white space.
        sep_forbidden = re.compile(r'\w|\s')
        for sep in separators:
            if re.search(sep_forbidden, sep) is not None:
                raise ValueError("The separator '{}' either contains whitespace, or some character that is reserved"
                                 " for keywords and identifiers!".format(sep))

        pattern_sep = '|'.join(re.escape(s) for s in reversed(sorted(separators, key=len)))

        spec_split = [(TokenType.EOS, r'$'),  # Match the end of the input.
                      (TokenType.COMMENT, re.escape('#') + r'[^\n]*\n'),
                      (TokenType.WHITESPACE, r'\s+'),  # Any white space sequence.
                      (TokenType.LITERAL, r'(\d+(\.\d*)?)|".+"'),  # integer, decimal, or string.
                      (TokenType.KEYWORD, '({sep})|(({kw}){nocont})'.format(sep=pattern_sep,
                                                                            kw=pattern_keyword,
                                                                            nocont=r'(?!\w)')),
                      (TokenType.IDENTIFIER, pattern_identifier)
                     ]

        pattern = "|".join('(?P<type%d>%s)' % pair for pair in spec_split)

        self._automaton = re.compile(pattern)
        self._skip_comments = skip_comments
        self._skip_whitespace = skip_whitespace

    def match_prefix(self, buffer, first=0):
        """
        Returns the longest valid token that is a prefix of the given buffer string.
        :param buffer: A string object that represents a slice of a larger input stream.
        :param first: The offset within the given buffer string at which matches should start.
        :exception LexError: If no prefix of the given buffer string is a valid token, or if buffer_final is False
                             and the longest valid prefix token ends at the end of the buffer.
        :return: A tuple (first, t, s, first + len(s)),
                 where first is the offset of the token inside the given buffer string,
                 t is the TokenType of the token that was matched
                 and s is the original input text that represents this token.
        """

        while True:
            m = self._automaton.match(buffer, pos=first)

            if m is None:
                raise LexError(LexErrorReason.UNKNOWN)

            ttype = TokenType(int(m.lastgroup[-1:]))
            string = m.group()

            if (self._skip_comments and ttype == TokenType.COMMENT) \
            or (self._skip_whitespace and ttype == TokenType.WHITESPACE):
                first += len(string)
                continue

            return first, ttype, string, first + len(string)


class Lexer:
    """
    A lexer makes a sequence of characters available as a sequence of tokens, to be processed by a parser.
    """

    def __init__(self, spec, source):
        """
        Creates a new lexer.
        :param spec: A LexerSpecification.
        :param source:
        """
        self._spec = check_type(spec)
        self._source = check_type(source, io.TextIOBase)
        self._eos = False
        self._buffer = io.StringIO()
        self._buffer_offset = 0
        self._buffer_length = 0
        self._pos = 0
        self._peek = None

    def peek(self):
        """
        Retrieves the token the lexer is currently seeing, without advancing to the next token.
        :return: A pair (t, s) consisting of TokenType t and token text s. When the end of the input has been reached,
                 this method returnes the token type EOS.
        """
        if self._peek is None:

            while True:
                first, t, s, end = self._spec.match(self._buffer.getvalue(),
                                                    self._buffer_offset,
                                                    self._eos)

                if end == self._buffer_length and not self._eos:
                    if self._buffer_offset > 0:
                        self._buffer = io.StringIO(self._buffer.getvalue()[self._buffer_offset:])
                        self._buffer_offset = 0
                    line = self._source.readline()
                    if len(line) == 0:
                        self._eos = True
                    else:
                        self._buffer.write(line)
                        self._buffer_length += len(line)
                else:
                    break

            self._peek = (t, s)

        return self._peek

    @property
    def eos(self):
        """
        Indicates if there are tokens left in the input to this lexer.
        """
        # Note that self._eos indicates whether the *source stream* ran out of *characters* !
        return self.peek()[0] == TokenType.EOF

    def read(self):
        """
        Retrieves the token the lexer is currently seeing, and advances to the next token.
        :exception StopIteration: If there are no more tokens left in the input.
        :return: A pair (t, s) consisting of TokenType t and token text s.
        """
        if self.eos:
            raise LexError(LexErrorReason.OUTOFTOKENS)

        t = self.peek()
        self._peek = None
        return t

    # TODO: Continue the rewrite from here downwards:

    def match(self, p):
        """
        Asserts that the token the lexer is currently seeing satisfies the given predicate, retrieves it and
        advances to the next token.
        :param p: The predicate to be satisfied by the token to be retrieved. It may raise a ValueError instead of
                  returning False.
        :exception StopIteration: If there are no more tokens left in the input.
        :exception ValueError: If the token to be retrieved does not satisfy the given predicate.
        :return: A pair (t, s) consisting of TokenType t and token text s.
        """
        if self.eos:
            raise StopIteration("No tokens left in the input!")

        t = self.peek()
        if not p(t):
            raise ValueError("Encountered an unexpected token!")
        return self.read()

    def seeing(self, p):
        """
        Decides whether the token the lexer is currently seeing satisfies the given predicate.
        :param p: The predicate to be satisfied.
        :exception StopIteration: If there are no more tokens left in the input.
        :return: A boolean value.
        """
        if self.eos:
            raise StopIteration("No tokens left in the input!")

        t = self.peek()
        try:
            return p(t)
        except ValueError:
            return False


def expected(s=None, t=None):
    """
    Constructs a predicate asserting that a given token has the specified type and text.
    :param t: The expected TokenType.
    :param s: The expected text of the token.
    :return: A pair (p, msg) consisting of a procedure p that maps tokens to boolean values and a message msg that
             can be used to indicate that the predicate was not met.
    """
    def p(f):
        ft, fs, _ = f
        if not ((t is None or ft == t) and (s is None or fs == s)):
            raise ValueError("Expected ({et}, {es}), but encountered ({ft}, '{fs}')"
                               .format(es="'" + s + "'" if s is not None else "*",
                                       et=t if t is not None else "*", fs=fs, ft=ft))
        return True

    return p


def keyword(s=None):
    """
    Constructs a predicate asserting that a given token is the expected keyword.
    :param s: The expected text of the token.
    :return: A pair (p, msg) consisting of a procedure p that maps tokens to boolean values and a message msg that
             can be used to indicate that the predicate was not met.
    """
    return expected(t=TokenType.KEYWORD, s=s)


def identifier(s=None):
    """
    Constructs a predicate asserting that a given token is an identifier.
    :param s: The expected text of the token.
    :return: A pair (p, msg) consisting of a procedure p that maps tokens to boolean values and a message msg that
             can be used to indicate that the predicate was not met.
    """
    return expected(t=TokenType.IDENTIFIER, s=s)


def literal():
    """
    Constructs a predicate asserting that a given token is a literal.
    :return: A pair (p, msg) consisting of a procedure p that maps tokens to boolean values and a message msg that
             can be used to indicate that the predicate was not met.
    """
    return expected(t=TokenType.LITERAL)
