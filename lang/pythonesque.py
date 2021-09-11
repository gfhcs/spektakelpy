import re
from enum import Enum

from lang.lexer import LexicalGrammar, LexError, LexErrorReason
from lang.tokens import TokenPosition


class TokenType(Enum):
    """
    The types of tokens that a Pythonesque lexer might produce, some of them only internally.
    """
    LINEEND_PREFIX = 100  # An incomplete end of a line, i.e. a sequence that
                          # *might* be continued to form the end of a line. Never emitted by the lexer.
    LINEEND = 101  # The end of a line, possibly including white space and line comments,
                   # but definitely a newline sequence. Never emitted by the lexer.
    HSPACE = 102  # A white space string without newlines. Never emitted by the lexer.
    LINEJOIN = 103  # An explicit line join token. Never emitted by the lexer.

    COMMENT = 1  # A line comment. Never emitted by the lexer.
    IDENTIFIER = 2  # An identifier.
    KEYWORD = 3  # A keyword.
    LITERAL = 4  # A complete literal
    LITERAL_PREFIX = 5  # A string that could be a prefix of a literal,
                        # but is definitely not a complete literal. Never emitted by the lexer.
    NEWLINE = 6  # A newline sequence, i.e. the end of a line and the start of a new line.
    INDENT = 7  # Represents an increase of the indendation level.
    DEDENT = 8  # Represents a decrease of the indendation level.
    END = 9  # The end of the source stream.

    def __repr__(self):
        s = super().__repr__()
        return s[s.find(".") + 1:]

    def __str__(self):
        s = super().__str__()
        return s[s.find(".") + 1:]


class PythonesqueLexicalGrammar(LexicalGrammar):
    """
    A lexical grammar that can be used for Python-like languages.
    It implements most principles from https://docs.python.org/3/reference/lexical_analysis.html
    """

    def __init__(self, keywords, separators, chunk_size):
        """
        Compiles a regular expression for lexing a Python-like language that has the given keywords and separators.
        :param keywords: The strings that are to be lexed as keyword tokens.
                         They must contain only alphanumeric characters and the underscore and they
                         must not start with a digit.
        :param separators: The strings that are to be lexed as separators. Separators have the same token type
                           as keywords, but unlike keywords they cannot be substrings of identifier or keyword tokens.
        """

        # This code is loosely based on https://docs.python.org/3/library/re.html#writing-a-tokenizer

        pattern_identifier = r'(?!\d)\w+'

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

        if chunk_size < 2:
            raise ValueError("Chunk size must be at least 2, for lexing explicit line joins!")
        if chunk_size < 1:
            raise ValueError("Chunk size must be positive!")

        mincs = max(map(len, separators))
        if chunk_size < mincs:
            raise ValueError("The chunk size {} is too short for the given"
                             " set of keywords and separators! It must be at least {}!".format(chunk_size, mincs))

        spec_split = [
            # The _PREFIX categories are necessary, because we need to buffer the source input in a StringIO object:
            # At the end of the buffer, we might not have managed to match a complete token (yet!), or we might be
            # considering the 'wrong' token type. In both cases, the continuation of the buffer would change the result.
            # This is why we need _PREFIX types, to make sure two things:
            # 1. There is a maximum number of characters after which we are guaranteed to match SOMETHING.
            # 2. If we are looking at an 'incomplete' token, the match will extend up to the end of the buffer,
            #    s.t. we can detect that we should extend the buffer.
            # Note that patterns will be matched with a precedence of the order in which they are listed.
            #
            # The end of a physical line:
            (TokenType.LINEEND, r' *(#[^\n]*)?(\n|\Z)'),
            # A prefix of a lineend:
            (TokenType.LINEEND_PREFIX, r' +\Z| *#[^\n]*\Z'),
            # Horizontal space, i.e. a sequence of space characters:
            (TokenType.HSPACE, r' +'),
            # Explicit join of physical lines:
            (TokenType.LINEJOIN, r'\\\n'),
            # Complete literals (integers, decimals, or strings):
            (TokenType.LITERAL, r'(\d+(?!(\d|\.)))|(\d+\.\d+)|"([^"\\\n]|(\\.))*"(?!")|"""("?"?([^"\\]|(\\.)))*"""'),
            # A prefix that definitely needs to be continued in order to become a valid literal:
            (TokenType.LITERAL_PREFIX, r'(\d+\.?\Z)|"([^"\\\n]|(\\.))*\Z|"""("?"?([^"\\]|(\\.)))*("?"?\Z)'),
            # Alphanumeric keywords:
            (
            TokenType.KEYWORD, '({sep})|(({kw}){nocont})'.format(sep=pattern_sep, kw=pattern_keyword, nocont=r'(?!\w)')),
            # Identifiers:
            (TokenType.IDENTIFIER, pattern_identifier)
        ]

        self._pattern = re.compile("|".join('(?P<t%d>(%s))' % (t.value, p) for t, p in spec_split))
        self._chunk_size = chunk_size

    @property
    def type_end(self):
        return TokenType.END

    @property
    def pattern(self):
        """
        The compile regular expression this grammar uses for matching raw (sub-)tokens.
        """
        return self._pattern

    def generate_tokens(self, buffer):

        # This code follows https://docs.python.org/3/reference/lexical_analysis.html

        pos = TokenPosition(0, 0, 0)  # What's our position in the input stream?
        istack = [0]  # The stack of indendation depths.
        bdepth = 0  # How deep are we nested in parentheses?

        def advance(t, s):
            nonlocal pos
            o, l, c = pos
            n = len(s)

            if t in (TokenType.LINEEND, TokenType.LINEJOIN):
                pos = TokenPosition(o + n, l + 1, 0)
            elif t == TokenType.LITERAL and s.startswith("\"\"\""):
                l -= 1
                for line in s.splitlines():
                    l += 1
                pos = TokenPosition(o + n, l, 0 + len(line))
            else:
                pos = TokenPosition(o + n, l, c + n)

        while True:

            try:
                # Important: The following call will never silently "skip" input. We get to see *every* bit of input
                #            in some output of the call!
                #            Also, the 'text' contains a newline if and only if 'kind' is TokenType.NEWILNE.

                kind, text = buffer.match_prefix(self._pattern, self._chunk_size)
            except EOFError:
                # Properly end the line, if necessary:
                if pos.column > 0:
                    yield TokenType.NEWLINE, "\n", pos

                # Generate DEDENT tokens until indendation stack is back to where it was at the beginning of the input.
                while len(istack) > 1:
                    yield TokenType.DEDENT, None, pos
                    istack.pop()

                yield TokenType.END, None, pos
                return

            if kind is not None:
                assert kind.startswith("t")
                kind = TokenType(int(kind[1:]))

            # Handle indendation, as described in https://docs.python.org/3/reference/lexical_analysis.html#indentation
            if pos.column == 0 and bdepth == 0 and kind != TokenType.LINEEND:
                if kind == TokenType.HSPACE:
                    i = len(text)
                else:
                    i = 0

                if i > istack[-1]:
                    istack.append(i)
                    yield TokenType.INDENT, None, pos
                else:
                    while i < istack[-1]:
                        yield TokenType.DEDENT, None, pos
                        istack.pop()

            if kind is None or kind == TokenType.LITERAL_PREFIX:
                raise LexError(LexErrorReason.INVALIDINPUT, pos)
            elif kind in (TokenType.LINEJOIN, TokenType.COMMENT):
                # Comments or explicit line joins should not be passed on.
                advance(kind, text)
            elif kind == TokenType.HSPACE:
                advance(kind, text)
            elif kind == TokenType.LINEEND:
                if pos.column == 0 or bdepth > 0:
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
