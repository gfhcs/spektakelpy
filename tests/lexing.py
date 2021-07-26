import unittest
from io import StringIO
from syntax import lexer

kw_python = ["False", "await", "else", "import", "pass", "None", "break", "except", "in", "raise", "True", "class",
             "finally", "is", "return", "and", "continue", "for", "lambda", "try", "as", "def", "from", "nonlocal",
             "while", "assert", "del", "global", "not", "with", "async", "elif", "if", "or", "yield"]
sep_python = ["+", "-", "*", "**", "/", "//", "%", "@", "<<", ">>", "&", "|", "^", "~", ":=", "<", ">", "<=", ">=",
              "==", "!=", "(", ")", "[", "]", "{", "}", ",", ":", ".", ";", "@", "=", "->", "+=", "-=", "*=", "/=",
              "//=", "%=", "@=", "&=", "|=", "^=", ">>=", "<<=", "**="]

sample_python1 = """
def perm(l):
        # Compute the list of all permutations of l
    if len(l) <= 1:
                  return [l]
    r = []
    for i in range(len(l)):
             s = l[:i] + l[i+1:]
             p = perm(s)
             for x in p:
              r.append(l[i:i+1] + x)
    return r
"""


def lex(spec, sample):
    """
    Turns a string into a sequence of tokens, using the given lexical grammar.
    :param spec: The LexicalGrammar to use for lexing.
    :param sample: A string that is to be lexed.
    :return: A list of tokens.
    """
    sample = StringIO(sample)
    l = lexer.Lexer(spec, sample)
    tokens = []
    while not l.seeing(lexer.end()):
        tokens.append(l.read())
    return tokens


def match(pattern, sample, chunk_size):
    """
    Turns a string into a sequence of raw matches, using the given lexical grammar.
    This is NOT actual lexing. Instead, only the BufferedMatchStream is tested.
    :param pattern: A compiled regular expression (re) used for matching.
    :param sample: A string that is to be processed.
    :param chunk_size: The chunk size to be used for buffering.
    :return: A list of pairs (kind, text).
    """
    buffer = lexer.BufferedMatchStream(StringIO(sample))
    matches = []
    while True:
        try:
            m = buffer.match_prefix(pattern, chunk_size)
        except EOFError:
            break

        if m[0] is None:
            raise lexer.LexError(lexer.LexErrorReason.INVALIDINPUT)

        matches.append(m)

    return matches


class TestPythonLexer(unittest.TestCase):

    def setUp(self):
        self._specs_python = []
        for cs in (1024, 3, 5, 7):
            self._specs_python.append((lexer.PythonesqueLexicalGrammar(kw_python, sep_python, cs), cs))

    def tokens_equal(self, reference, tokens):
        """
        Asserts that the given token list equals the reference.
        :param reference: A list of tokens that must be matched.
        :param tokens: A list of tokens that must match the reference.
        """
        self.assertEqual(len(reference), len(tokens), "Number of emitted tokens does not match the reference!")
        for (rt, rs, _), (t, s, _) in zip(reference, tokens):
            self.assertEqual(rt, t)
            self.assertEqual(rs, s)

    def test_empty(self):
        for s, cs in self._specs_python:
            with self.subTest(chunk_size=cs):
                tokens = lex(s, "")
                self.tokens_equal([], tokens)

    def test_buffer_allwhite(self):
        text = "   \n \n\n   # This is a comment \n\n \n #Another ocmment .\n\n    \n"

        reference = [("t101", "   \n"),
                     ("t101", " \n"),
                     ("t101", "\n"),
                     ("t101", "   # This is a comment \n"),
                     ("t101", "\n"),
                     ("t101", " \n"),
                     ("t101", " #Another ocmment .\n"),
                     ("t101", "\n"),
                     ("t101", "    \n")]

        for s, cs in self._specs_python:
            with self.subTest(chunk_size=cs):
                matches = match(s.pattern, text, chunk_size=cs)
                self.assertListEqual(reference, matches)

    def test_allwhite(self):
        for s, cs in self._specs_python:
            with self.subTest(chunk_size=cs):
                tokens = lex(s, "   \n \n\n   # This is a comment \n\n \n #Another ocmment .\n\n    \n")
                self.tokens_equal([], tokens)
