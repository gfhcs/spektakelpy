import unittest
from io import StringIO

from syntax.phrasal import spektakel, ast


def parse(sample):
    """
    Parses a string as a Spektakel program, i.e. lexes it, parses it and returns the resulting abstract syntax tree.
    :exception ParserError: If the given string was not a syntactically correct Spektakel program.
    :param sample: A string that is to be lexed and parsed.
    :return: A Node object.
    """
    sample = StringIO(sample)
    lexer = spektakel.SpektakelLexer(sample)
    return spektakel.SpektakelParser.parse_block(lexer)


class TestSpektakelParser(unittest.TestCase):

    def test_empty(self):
        """
        Tests that the empty input stream is parsed correctly.
        """

        samples = ["", "      ", "   # Hello world!\n # This is some fun text :-)\n\n  \n # Some more text."]

        for idx, s in enumerate(samples):
            with self.subTest(idx=idx):
                n = parse(s)
                self.assertIsInstance(n, ast.Block)
                self.assertEquals(len(n.children), 0)

