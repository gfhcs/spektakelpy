from enum import Enum


class TokenType(Enum):
    """
    Describes types of syntactic tokens.
    """
    IDENTIFIER = 0
    KEYWORD = 1
    LITERAL = 2
    EOF = 4

# TODO: "+" should actually be a default separator.
# CAUTION: Making it one will break Gereon's caches, because we used to allow + in CVF identifiers.
# CONSEQUENTLY: We should have a proper definition for what a CVF identifier is allowed to be.
#               SIMILARLY for other things that have names! Essentially we should say that they need to be lexable
#               identifiers!
default_separators = ["(", ")", "-", "True", "False", "[", "]", "{", "}", ",", "=", "%"]


# TODO: lex should use StringIO to build up tokens. This would probably be more efficient.

def lex(characters, separators=default_separators):
    """
    Turns an iterable of characters into an iterable of tokens.
    :param separators: A collection of strings that are considered token terminators.
    :param characters: An iterable of characters.
    :return: An iterable of triples (t, s, p),  t is a TokenType
    and s is either the token string, or, in the case of literals, the value represented by the token. r is the position
    of the token in the input stream.
    """

    t = None
    s = ""
    p = None
    source = enumerate(characters)
    pos = None
    c = None
    advance = True

    kwc = None

    try:
        while True:

            if advance and t != TokenType.KEYWORD:
                pos, c = next(source)

            advance = True

            if t is None:
                if c.isspace():
                    continue
                try:
                    int(c)
                    t = TokenType.LITERAL
                    s += c
                    p = pos
                except ValueError:
                    t = TokenType.IDENTIFIER
                    advance = False
                    p = pos
            elif t == TokenType.KEYWORD:
                kwc = list(filter(lambda sep: sep.startswith(s), kwc if kwc is not None else separators))

                if len(kwc) == 0:
                    yield (t, s[:-1], p)
                    c = s[-1]
                    advance = False
                elif len(kwc) == 1:
                    yield (t, s, p)
                else:
                    pos, cc = next(source)
                    s += cc
                    continue

                p = None
                kwc = None
                t = None
                s = ""

            elif t == TokenType.LITERAL:
                try:
                    try: # Is c a special float character?
                        fchars = ".e-"
                        x = fchars.index(c)
                    except ValueError:  # No, it is not a special float character.
                        x = -1

                    if x >= 0:
                        if (x == 0 or fchars[x - 1] in s) and c not in s:
                            pass
                        else:
                            raise ValueError("Encountered invalid numeric literal with prefix {p}".format(p=s + c))
                    else:
                        int(c)
                    s += c
                    continue
                except ValueError:
                    advance = False
                    yield (t, s, p)
                    t = None
                    s = ""
                    p = None
                    continue
            elif t == TokenType.IDENTIFIER:
                if c.isspace():
                    yield (t, s, p)
                    t = None
                    s = ""
                    p = None
                    continue
                s += c
                for sep in separators:
                    if s.endswith(sep):
                        identifier = s[:-len(sep)]
                        if len(identifier) > 0:
                            yield (t, identifier, p)
                        s = sep
                        t = TokenType.KEYWORD
                        p += len(identifier)
                        break

    except StopIteration:
        if t is not None:
            yield (t, s, p)
        yield (TokenType.EOF, "", pos + 1)


class Lexer:
    """
    Supports the parsing of tokens.
    """

    def __init__(self, source, separators=default_separators):
        self._separators = separators
        self._lex = iter(lex(source, separators=separators))
        self._peek = None

    @property
    def position(self):
        """
        The number of characters that have been consumed by this lexer so far, in order to read tokens.
        """
        return self.peek()[2]

    def peek(self):
        """
        Retrieves the token the lexer is currently seeing, without advancing to the next token.
        :return: A pair (t, s) consisting of TokenType t and token text s, or None, if there are not more tokens in the
        input.
        """
        if self._peek is None:
            self._peek = next(self._lex)
        return self._peek

    def read(self):
        """
        Retrieves the token the lexer is currently seeing, and advances to the next token.
        :exception StopIteration: If there are no more tokens left in the input.
        :return: A pair (t, s) consisting of TokenType t and token text s.
        """
        if self.eos:
            raise StopIteration("No tokens left in the input!")

        t = self.peek()
        self._peek = None
        return t

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

    def __iter__(self):
        while not self.eos:
            yield self.read()

    @property
    def eos(self):
        """
        Indicates if there are tokens left in the input to this lexer.
        """
        return self.peek()[0] == TokenType.EOF


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
