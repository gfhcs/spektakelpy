import unittest
from io import StringIO
from syntax import lexer
from . import samples_python

kw_python = ["False", "await", "else", "import", "pass", "None", "break", "except", "in", "raise", "True", "class",
             "finally", "is", "return", "and", "continue", "for", "lambda", "try", "as", "def", "from", "nonlocal",
             "while", "assert", "del", "global", "not", "with", "async", "elif", "if", "or", "yield"]
sep_python = ["+", "-", "*", "**", "/", "//", "%", "@", "<<", ">>", "&", "|", "^", "~", ":=", "<", ">", "<=", ">=",
              "==", "!=", "(", ")", "[", "]", "{", "}", ",", ":", ".", ";", "@", "=", "->", "+=", "-=", "*=", "/=",
              "//=", "%=", "@=", "&=", "|=", "^=", ">>=", "<<=", "**="]


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
        """
        Tests that the empty input stream does not cause any trouble.
        """
        for s, cs in self._specs_python:
            with self.subTest(chunk_size=cs):
                tokens = lex(s, "")
                self.tokens_equal([], tokens)

    def test_buffer_allwhite(self):
        """
        Tests the BufferedMatchStream on an input sequence that consists of various flavors of empty lines.
        """

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
        """
        Tests the lexer on an input sequence that consists of various flavors of empty lines.
        """
        for s, cs in self._specs_python:
            with self.subTest(chunk_size=cs):
                tokens = lex(s, "   \n \n\n   # This is a comment \n\n \n #Another ocmment .\n\n    \n")
                self.tokens_equal([], tokens)

    def test_simple_samples(self):
        """
        Tests the lexer on several simple Python programs.
        """

        for sk, (code, reference) in samples_python.items():
            for s, cs in self._specs_python:
                with self.subTest(sample=sk, chunk_size=cs):
                    tokens = lex(s, code)
                    self.tokens_equal(reference, tokens)
