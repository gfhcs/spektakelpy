from enum import Enum
from typing import NamedTuple


class TokenType(Enum):
    """
    Describes types of syntactic tokens.
    """
    LINEEND_PREFIX = 100  # An incomplete end of a line, i.e. a sequence that
                          # *might* be continued to form the end of a line. Never emitted by the lexer.
    LINEEND = 101  # The end of a line, possibly including white space and line comments,
                   # but definitely a newline sequence. Never emitted by the lexer.
    HSPACE = 102  # A white space string without newlines. Never emitted by the lexer.
    LINEJOIN = 103  # An explicit line join token. Never emitted by the lexer.

    COMMENT = 1  # A line comment.
    IDENTIFIER = 2  # An identifier.
    KEYWORD = 3  # A keyword.
    LITERAL = 4  # A complete literal
    LITERAL_PREFIX = 5  # A string that could be a prefix of a literal, but is definitely not a complete literal.
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


class TokenPosition(NamedTuple):
    offset: int
    line: int
    column: int

    def __str__(self):
        return "Line {}, column {}".format(self.line + 1, self.column + 1)

    def __repr__(self):
        return "Line {}, column {}".format(self.line + 1, self.column + 1)