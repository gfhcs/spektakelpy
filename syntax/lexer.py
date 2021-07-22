import io
import re
from enum import Enum
from typing import NamedTuple
from util import check_type


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


class TokenType(Enum):
    """
    Describes types of syntactic tokens.
    """
    LINEJOIN = -3  # An explicit line join token. Never emitted by the lexer.
    HSPACE = -2  # A white space string without newlines. Never emitted by the lexer.
    LINEEND = -1   # The end of a line, possibly including white space and line comments,
                   # but definitely a newline sequence. Never emitted by the lexer.
    COMMENT = 1  # A line comment.
    IDENTIFIER = 2  # An identifier.
    KEYWORD = 3  # A keyword.
    LITERAL = 4  # A complete literal
    LITERAL_PREFIX = 5  # A string that could be a prefix of a literal, but is definitely not a complete literal.
    NEWLINE = 6  # A newline sequence, i.e. the end of a line and the start of a new line.
    INDENT = 7  # Represents an increase of the indendation level.
    DEDENT = 8  # Represents a decrease of the indendation level.
    END = 9  # The end of the source stream.


def compile_pattern(keywords, separators):
    """
    Compiles a regular expression for the given keywords and separators. This regular expression matches tokens
    that a parser can use to parse various formal languages.
    :param keywords: The strings that are to be lexed as keyword tokens.
                     They must contain only alphanumeric characters and the underscore and they
                     must not start with a digit.
    :param separators: The strings that are to be lexed as separators. Separators have the same token type
                       as keywords, but unlike keywords they cannot be substrings of identifier or keyword tokens.
    """

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

    spec_split = [
                  (TokenType.LINEEND, r'( *\n)|( *#[^\n]*\n)'), # The end of a physical line.
                  (TokenType.HSPACE, r' +'),  # Horizontal space, i.e. a sequence of space characters.
                  (TokenType.LINEJOIN, r'\\\n'),
                  (TokenType.LITERAL, r'(\d+(\.\d+)?)|"([^"\\\n]|(\\.))*"|"""([^"\\]|(\\.))*"""'),  # integer, decimal, or string.
                  (TokenType.LITERAL_PREFIX, r'(\d+\.(?!\d)|"([^"\\\n]|(\\.))*(?!")|"""([^"\\]|(\\.))*(?!")'), # A prefix that definitely needs to be continued in order to become a valid literal.
                  (TokenType.KEYWORD, '({sep})|(({kw}){nocont})'.format(sep=pattern_sep,
                                                                        kw=pattern_keyword,
                                                                        nocont=r'(?!\w)')),
                  (TokenType.IDENTIFIER, pattern_identifier)
                 ]

    pattern = "|".join('(?P<type%d>%s)' % pair for pair in spec_split)

    return re.compile(pattern)


class BufferedMatchStream:
    """
    Buffers a TextIOBase stream in a way that allows tokenization according to a regular expression.
    """

    def __init__(self, source):
        """
        Buffers a TextIOBase object.
        :param source: The TextIOBase oject that is to be buffered.
        """
        self._source = check_type(source, io.TextIOBase)
        self._buffer = io.StringIO('')
        self._buffer_offset = 0
        self._buffer_length = 0

    def match_prefix(self, pattern, chunk_size=1024):
        """
        Consumes the longest possible prefix of the buffered stream that is valid according to the given regular
        expression pattern.
        :param pattern: A compiled regular expresssion
        :param chunk_size: The number of characters that should be consumed from the input stream at once. This number
                           must be so large that if a chunk of this size does not have a prefix matching the pattern,
                           there cannot be any continuation of that chunk that would lead to the existence of such a
                           prefix.
        :exception EOFError: If not enough input remains in the source stream.
        :return: A pair (k, s), where k is the name of the regular expression group that matched a prefix
                 and s is the text of the prefix. If no prefix of the remaining source input matches the given pattern,
                 (None, "") is returned.
        """

        while True:

            m = pattern.match(self._buffer.getvalue(), pos=self._buffer_offset)

            if m is not None and m.end() < self._buffer_length:
                # Valid token ends before the end of the buffer. Must be a complete token.
                # Mark the range of m as consumed:
                t = m.group(0)
                self._buffer_offset += len(t)
                return m.lastgroup, t
            else:
                # Either there is no prefix of the buffer that matches the pattern, or the match ends at the end of
                # the buffer. In both cases it might be possible to continue the buffer, such that a new, valid match
                # happens. So we want to try to continue the buffer.

                if m is None:
                    # No valid match found so far, so we would need to continue the buffer to find one.
                    if self._buffer_length - self._buffer_offset >= chunk_size:
                        # We assume that the chunk size is sufficiently large, so in this case there is no hope.
                        return None, ""
                    if self._source is None:
                        # We would need to consume more input, but there is none left!
                        if self._buffer_length - self._buffer_offset == 0:
                            # We're exactly at the end, i.e. we properly matched *all* the input and are done.
                            raise EOFError("No prefix of the remaining input matches the given pattern!")
                        else:
                            # There is some remaining input that cannot be matched anymore.
                            return None, ""

                    # Otherwise we want to try and continue the buffer.
                else:
                    # We already have a match, but maybe continuing the buffer would continue the match?
                    pass

                # Before we extend the buffer, we discard all the stuff we've already read:
                if self._buffer_offset > 0:
                    self._buffer = io.StringIO(self._buffer.getvalue()[self._buffer_offset:])
                    self._buffer_length -= self._buffer_offset
                    self._buffer_offset = 0

                # Now extend the buffer:
                chunk = self._source.read(chunk_size)
                if len(chunk) < chunk_size:
                    self._source = None
                self._buffer.write(chunk)
                self._buffer_length += len(chunk)


class TokenPosition(NamedTuple):
    offset: int
    line: int
    column: int


def lex(pattern, buffer):
    """
    A generator for tokens lexed from a character stream.
    :param pattern: A compile 're' pattern, that matches 'raw' tokens, as returned from compile_pattern.
    :param buffer: A BufferedMatchStream the contents of which will be tokenized.
    :return: A generator of triples (kind, text, position) that represent the tokens that were lexed.
    """

    # This code follows https://docs.python.org/3/reference/lexical_analysis.html

    pos = TokenPosition(0, 0, 0)  # What's our position in the input stream?
    istack = [0]  # The stack of indendation depths.
    bdepth = 0  # How deep are we nested in parentheses?

    def advance(t, s):
        nonlocal pos
        o, l, c = pos
        n = len(s)

        if t in (TokenType.LINEEND, TokenType.LINEJOIN):
            pos = (o + n, l + 1, 0)
        elif t == TokenType.LITERAL and s.startswith("\"\"\""):
            l -= 1
            for line in s.splitlines():
                l += 1
            pos = (o + n, l, 0 + len(line))
        else:
            pos = (o + n, l, c + n)

    while True:

        try:
            # Important: The following call will never silently "skip" input. We get to see *every* bit of input
            #            in some output of the call!
            #            Also, the 'text' contains a newline if and only if 'kind' is TokenType.NEWILNE.

            kind, text = buffer.match_prefix(pattern)
        except EOFError:
            # Generate DEDENT tokens until indendation stack is back to where it was at the beginning of the input.
            while len(istack) > 1:
                yield TokenType.DEDENT, None, pos
                istack.pop()

            yield TokenType.END, None, pos
            return

        if kind is not None:
            kind = TokenType(int(kind))

        if kind is None or kind == TokenType.LITERAL_PREFIX:
            raise LexError(LexErrorReason.INVALIDINPUT, pos)
        elif kind in (TokenType.LINEJOIN, TokenType.COMMENT):
            # Comments or explicit line joins should not be passed on.
            advance(kind, text)
        elif kind == TokenType.HSPACE:
            if pos == 0 and bdepth == 0:
                # See https://docs.python.org/3/reference/lexical_analysis.html#indentation

                i = len(text)
                advance(kind, text)

                if i > istack[-1]:
                    istack.append(i)
                    yield TokenType.INDENT, None, pos
                else:
                    while i < istack[-1]:
                        yield TokenType.DEDENT, None, pos
                        istack.pop()
            else:
                advance(kind, text)
        elif kind == TokenType.LINEEND:
            if pos == 0 or bdepth > 0:
                # Empty lines, or line ends inside of braces are to be skipped.
                advance(kind, text)
            else:
                offset = text.find("\n")
                _o, _l, _c = pos
                yield TokenType.NEWLINE, "\n", TokenPosition(_o + offset, _l, _c + offset)
                advance(kind, text)
        else:
            if kind == TokenType.KEYWORD and text in ("(", "[", "{"):
                bdepth += 1
            elif kind == TokenType.KEYWORD and text in (")", "]", "}"):
                bdepth -= 1

            yield kind, text, pos
            advance(kind, text)


class Lexer:
    """
    A lexer makes a sequence of characters available as a sequence of tokens, to be processed by a parser.
    """

    def __init__(self, keywords, separators, source):
        """
        Creates a new lexer.
        :param keywords: The strings that are to be lexed as keyword tokens.
                         They must contain only alphanumeric characters and the underscore and they
                         must not start with a digit.
        :param separators: The strings that are to be lexed as separators. Separators have the same token type
                           as keywords, but unlike keywords they cannot be substrings of identifier or keyword tokens.
        :param source: A text stream providing input characters.
        """

        self._g = iter(lex(compile_pattern(keywords, separators), BufferedMatchStream(source)))
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
