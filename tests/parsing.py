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
                self.assertEqual(len(n.children), 0)

    def test_identifier(self):
        """
        Tests that simple identifiers are parsed correctly.
        """

        samples = ["x", "x\n\n", "helloworld", "\nhello_world"]

        for idx, s in enumerate(samples):
            with self.subTest(idx=idx):
                n = parse(s)
                self.assertIsInstance(n, ast.Block)
                self.assertEqual(len(n.children), 1)

                statement = n.children[0]

                self.assertIsInstance(statement, ast.ExpressionStatement)
                self.assertIsInstance(statement.children[0], ast.Identifier)

    def test_simple(self):
        """
        Tests that simple expressions are parsed correctly.
        """

        samples = {"(((x)))": ast.Identifier,
                   "\n3.1415926\n": ast.Constant,
                   "\"Hello world :-)\"": ast.Constant}

        for idx, (s, t) in enumerate(samples.items()):
            with self.subTest(idx=idx):
                n = parse(s)
                self.assertIsInstance(n, ast.Block)
                self.assertEqual(len(n.children), 1)

                statement = n.children[0]

                self.assertIsInstance(statement, ast.ExpressionStatement)
                self.assertIsInstance(statement.children[0], t)

    def test_application(self):
        """
        Tests that simple expressions are parsed correctly.
        """

        samples = {"x.y": ast.Attribute,
                   "x.y.z": ast.Attribute,
                   "x[5]": ast.Projection,
                   "x[\"hello\"]": ast.Projection,
                   "f(x)": ast.Call,
                   "f(x, y)": ast.Call,
                   "object.method(arg1, arg2)[index1][index2]": ast.Projection,
                   }

        for idx, (s, t) in enumerate(samples.items()):
            with self.subTest(idx=idx):
                n = parse(s)
                self.assertIsInstance(n, ast.Block)
                self.assertEqual(len(n.children), 1)

                statement = n.children[0]

                self.assertIsInstance(statement, ast.ExpressionStatement)
                self.assertIsInstance(statement.children[0], t)

    def test_async(self):
        """
        Tests that simple expressions are parsed correctly.
        """

        samples = {"async f(x)": ast.Launch,
                   "await async f(x)": ast.Await,
                   "async object.method(x)": ast.Launch,
                   "async x[5]": ast.Launch,
                   "async y": ast.Launch,
                   }

        for idx, (s, t) in enumerate(samples.items()):
            with self.subTest(idx=idx):
                n = parse(s)
                self.assertIsInstance(n, ast.Block)
                self.assertEqual(len(n.children), 1)

                statement = n.children[0]

                self.assertIsInstance(statement, ast.ExpressionStatement)
                self.assertIsInstance(statement.children[0], t)

