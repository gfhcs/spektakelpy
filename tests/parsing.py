import os.path
import unittest
from io import StringIO

from examples import paths as example_paths
from lang.lexer import LexError
from lang.parser import ParserError
from lang.spek import ast, syntax
from lang.spek.data.terms import ArithmeticBinaryOperator, BooleanBinaryOperator, ComparisonOperator, UnaryOperator
from tests.samples_general.large import samples as samples_large
from tests.samples_parsing.classes import samples as samples_class
from tests.samples_parsing.controlflow import samples as samples_controlflow
from tests.samples_parsing.procedures import samples as samples_def
from tests.samples_parsing.properties import samples as samples_prop
from tests.samples_parsing.tuples import samples as samples_tuples


def parse(sample):
    """
    Parses a string as a Spektakel program, i.e. lexes it, parses it and returns the resulting abstract syntax tree.
    :exception ParserError: If the given string was not a syntactically correct Spektakel program.
    :param sample: A string that is to be lexed and parsed.
    :return: A Node object.
    """
    sample = StringIO(sample)
    lexer = syntax.SpektakelLexer(sample)
    return syntax.SpektakelParser.parse_block(lexer)


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
                   "\"Hello world :-)\"": ast.Constant,
                   "True": ast.Constant,
                   "False": ast.Constant,
                   "None": ast.Constant}

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
        Tests that application expressions are parsed correctly.
        """

        samples = {"x.y": ast.Attribute,
                   "x.y.z": ast.Attribute,
                   "x[5]": ast.Projection,
                   "x[\"hello\"]": ast.Projection,
                   "f(x)": ast.Call,
                   "f(x, y)": ast.Call,
                   "object.method(arg1, arg2)[index1][index2]": ast.Projection,
                   "f(x == y)": ast.Call
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
        Tests that async/await expressions are parsed correctly.
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

    def test_pow(self):
        """
        Tests that exponentiation expressions are parsed correctly.
        """

        samples = {"x ** 2": ast.ArithmeticBinaryOperation,
                   "2 ** x": ast.ArithmeticBinaryOperation,
                   "(async f(x)) ** 2": ast.ArithmeticBinaryOperation,
                   "object.method(x, y) ** 2": ast.ArithmeticBinaryOperation,
                   "base(x) ** power(x)": ast.ArithmeticBinaryOperation,
                   }

        for idx, (s, t) in enumerate(samples.items()):
            with self.subTest(idx=idx):
                n = parse(s)
                self.assertIsInstance(n, ast.Block)
                self.assertEqual(len(n.children), 1)

                statement = n.children[0]

                self.assertIsInstance(statement, ast.ExpressionStatement)
                self.assertIsInstance(statement.children[0], t)

    def test_unary_minus(self):
        """
        Tests that unary minus expressions are parsed correctly.
        """

        samples = {"-42": ast.UnaryOperation,
                   "-x": ast.UnaryOperation,
                   "- async f(x)": ast.UnaryOperation,
                   "- f(x)": ast.UnaryOperation,
                   "- - ---x": ast.UnaryOperation
                   }

        for idx, (s, t) in enumerate(samples.items()):
            with self.subTest(idx=idx):
                n = parse(s)
                self.assertIsInstance(n, ast.Block)
                self.assertEqual(len(n.children), 1)

                statement = n.children[0]

                self.assertIsInstance(statement, ast.ExpressionStatement)
                self.assertIsInstance(statement.children[0], t)

    def test_mult(self):
        """
        Tests that product expressions are parsed correctly.
        """

        samples = {"x * y": ast.ArithmeticBinaryOperation,
                   "1 * 1": ast.ArithmeticBinaryOperation,
                   "a // b": ast.ArithmeticBinaryOperation,
                   "a / b": ast.ArithmeticBinaryOperation,
                   "x % r": ast.ArithmeticBinaryOperation,
                   "(a // b) * b": ast.ArithmeticBinaryOperation,
                   "(async f(x)) * 42": ast.ArithmeticBinaryOperation,
                   "(x * y) ** (kuno % 3)": ast.ArithmeticBinaryOperation,
                   }

        for idx, (s, t) in enumerate(samples.items()):
            with self.subTest(idx=idx):
                n = parse(s)
                self.assertIsInstance(n, ast.Block)
                self.assertEqual(len(n.children), 1)

                statement = n.children[0]

                self.assertIsInstance(statement, ast.ExpressionStatement)
                self.assertIsInstance(statement.children[0], t)

    def test_add(self):
        """
        Tests that summation expressions are parsed correctly.
        """

        samples = {"x + y": ArithmeticBinaryOperator.PLUS,
                   "1 + 1": ArithmeticBinaryOperator.PLUS,
                   "a - b": ArithmeticBinaryOperator.MINUS,
                   "a + b * b": ArithmeticBinaryOperator.PLUS,
                   "(a + b) * b": ArithmeticBinaryOperator.TIMES,
                   "(async f(x)) + 42": ArithmeticBinaryOperator.PLUS,
                   "(x + y) ** (kuno - 3)": ArithmeticBinaryOperator.POWER,
                   "a + b * a - b": ArithmeticBinaryOperator.MINUS,
                   "a + b * (a - b)": ArithmeticBinaryOperator.PLUS,
                   "(a + b) * (a - b)": ArithmeticBinaryOperator.TIMES,
                   }

        for idx, (s, t) in enumerate(samples.items()):
            with self.subTest(idx=idx):
                n = parse(s)
                self.assertIsInstance(n, ast.Block)
                self.assertEqual(len(n.children), 1)

                statement = n.children[0]

                self.assertIsInstance(statement, ast.ExpressionStatement)
                self.assertIsInstance(statement.children[0], ast.ArithmeticBinaryOperation)
                self.assertEqual(statement.children[0].operator, t)

    def test_comparison(self):
        """
        Tests that comparison expressions are parsed correctly.
        """

        samples = {"x > y": ComparisonOperator.GREATER,
                   "14 < pi": ComparisonOperator.LESS,
                   "x + y <= x ** 2 + y ** 2": ComparisonOperator.LESSOREQUAL,
                   "f(x)  + g(x) >= z(x)": ComparisonOperator.GREATEROREQUAL,
                   "x in (x, y, z)": ComparisonOperator.IN,
                   "E == m * c ** 2": ComparisonOperator.EQ,
                   "1 + 2 + 3 != 4": ComparisonOperator.NEQ,
                   "x in (a, b, c)": ComparisonOperator.IN,
                   "y not in samples": ComparisonOperator.NOTIN,
                   "m is None": ComparisonOperator.IS,
                   "m is not None": ComparisonOperator.ISNOT
                   }

        for idx, (s, t) in enumerate(samples.items()):
            with self.subTest(idx=idx):
                n = parse(s)
                self.assertIsInstance(n, ast.Block)
                self.assertEqual(len(n.children), 1)

                statement = n.children[0]

                self.assertIsInstance(statement, ast.ExpressionStatement)
                self.assertIsInstance(statement.children[0], ast.Comparison)
                self.assertEqual(statement.children[0].operator, t)

    def test_boolean(self):
        """
        Tests that boolean expressions are parsed correctly.
        """

        samples = {"True": None,
                   "False": None,
                   "not x": UnaryOperator.NOT,
                   "not not not x": UnaryOperator.NOT,
                   "f(x) == g(x) and a > b": BooleanBinaryOperator.AND,
                   "not (x and y) == (not x or not y)": UnaryOperator.NOT,
                   "(not (x and y)) == (not x or not y)": ComparisonOperator.EQ,
                   "not x and y": BooleanBinaryOperator.AND,
                   "not (x and y)": UnaryOperator.NOT,
                   }

        for idx, (s, t) in enumerate(samples.items()):
            with self.subTest(idx=idx):
                n = parse(s)
                self.assertIsInstance(n, ast.Block)
                self.assertEqual(len(n.children), 1)

                statement = n.children[0]

                self.assertIsInstance(statement, ast.ExpressionStatement)
                if t is not None:
                    self.assertEqual(statement.children[0].operator, t)

    def test_negative(self):
        """
        Lumps together all the test cases in which the parser should complain.
        """

        samples = ["not (x and y) == not x or not y",  # Must not work, because the second not cannot follow the == .
                   "a, 42 = f(x)"  # Must not work because 42 is not assignable.
                   "buffer_full().set(True)",  # Must fail because 'set' is a keyword that we use for properties.
                  ]

        for idx, s in enumerate(samples):
            with self.subTest(idx=idx):
                with self.assertRaises((LexError, ParserError)):
                    parse(s)

    def test_call_chain(self):
        """
        Tests the chaining of calls.
        """

        samples = ["buffer_full().foo(True)",
                   ]

        for idx, s in enumerate(samples):
            with self.subTest(idx=idx):
                n = parse(s)
                self.assertIsInstance(n, ast.Block)
                self.assertEqual(len(n.children), 1)

                statement = n.children[0]

                self.assertIsInstance(statement, ast.ExpressionStatement)

    def test_assignment(self):
        """
        Tests assignment statements.
        """

        samples = ["x = 42",
                   "(a, b) = 1, 2",
                   "a, b, c = 1, 2, 3",
                   "hello = world",
                   "a, b = f(x)",
                   "a, b, c = await async (3 * x + 12 * y)",
                   ]

        for idx, s in enumerate(samples):
            with self.subTest(idx=idx):
                n = parse(s)
                self.assertIsInstance(n, ast.Block)
                self.assertEqual(len(n.children), 1)

                statement = n.children[0]

                self.assertIsInstance(statement, ast.Assignment)

    def test_tuples(self):
        """
        Tests various ways of constructing tuples.
        """
        for idx, (s, t) in enumerate(samples_tuples.items()):
            with self.subTest(idx=idx):
                n = parse(s)
                self.assertIsInstance(n, ast.Block)

                if t is not None:
                    for statement in n.children:
                        self.assertIsInstance(statement, t)

    def test_import(self):
        """
        Tests import statements.
        """

        # Wildcards used to be supported, as in Python.
        # We stopped supporting them because they would require the validator to
        # recurse into the imported module, which we cannot do in general because
        # modules are not always defined by an AST.

        samples = ["import mymodule",
                   "import mymodule as m",
                   "from mymodule import name1, name2",
                   "from mymodule import name1 as n1, name2 as n2",
                   # "from mymodule import *",
                   "import mypackage.mymodule",
                   "import mypackage.mymodule as m",
                   "from mypackage.mymodule import name1, name2",
                   "from mypackage.mymodule import name1 as n1, name2 as n2",
                   # "from mypackage.mymodule import *"
                   ]

        for idx, s in enumerate(samples):
            with self.subTest(idx=idx):
                n = parse(s)
                self.assertIsInstance(n, ast.Block)
                self.assertEqual(len(n.children), 1)

                statement = n.children[0]

                self.assertIsInstance(statement, (ast.ImportNames, ast.ImportSource))

    def test_simple_statements(self):
        """
        Tests simple statements, like pass, break, continue and return.
        """

        samples = {"pass": ast.Pass,
                   "break": ast.Break,
                   "continue": ast.Continue,
                   "return": ast.Return,
                   "return m*c**2": ast.Return,
                   "return True": ast.Return,
                   "return False": ast.Return,
                   "raise": ast.Raise,
                   "raise DummyError()": ast.Raise
                   }

        for idx, (s, t) in enumerate(samples.items()):
            with self.subTest(idx=idx):
                n = parse(s)
                self.assertIsInstance(n, ast.Block)
                self.assertEqual(len(n.children), 1)

                statement = n.children[0]

                self.assertIsInstance(statement, t)

    def test_control_flow(self):
        """
        Tests control flow statements, like 'atomic', 'if', and 'while'.
        """

        for idx, (s, t) in enumerate(samples_controlflow.items()):
            with self.subTest(idx=idx):
                n = parse(s)
                self.assertIsInstance(n, ast.Block)

                if t is not None:
                    for statement in n.children:
                        self.assertIsInstance(statement, t)

    def test_prop(self):
        """
        Tests property declarations.
        """

        for idx, (s, t) in enumerate(samples_prop.items()):
            with self.subTest(idx=idx):
                n = parse(s)
                self.assertIsInstance(n, ast.Block)

                if t is not None:
                    for statement in n.children:
                        self.assertIsInstance(statement, t)

    def test_def(self):
        """
        Tests procedure declarations.
        """

        for idx, (s, t) in enumerate(samples_def.items()):
            with self.subTest(idx=idx):
                n = parse(s)
                self.assertIsInstance(n, ast.Block)

                if t is not None:
                    for statement in n.children:
                        self.assertIsInstance(statement, t)

    def test_class(self):
        """
        Tests class declarations.
        """

        for idx, (s, t) in enumerate(samples_class.items()):
            with self.subTest(idx=idx):
                n = parse(s)
                self.assertIsInstance(n, ast.Block)

                if t is not None:
                    for statement in n.children:
                        self.assertIsInstance(statement, t)

    def test_large(self):
        """
        Tests larger samples.
        """

        for idx, s in enumerate(samples_large):
            with self.subTest(idx=idx):
                n = parse(s)
                self.assertIsInstance(n, ast.Block)

    def test_examples(self):
        """
        Tests the parser on all spek examples.
        """
        for path in example_paths:
            _, filename = os.path.split(path)
            with self.subTest(example=os.path.splitext(filename)[0]):
                with open(path, 'r') as sample:
                    lexer = syntax.SpektakelLexer(sample)
                    syntax.SpektakelParser.parse_block(lexer)
