import os.path
import unittest

from examples import paths as example_paths
from lang.environment import Environment
from lang.spek import syntax, static
from io import StringIO


def validate(sample, env=None):
    """
    Lexes, parses and validates the given code sample.
    :param env: The environment in which the AST of the given sample is to be validated.
    :exception ParserError: If the given string was not a syntactically correct Spektakel program.
    :param sample: The code to lex, parse and validate, as a string.
    :return: A tuple (node, env, dec, err), where node is the AST representing the code, env is an environment mapping
             names to their declarations, dec is a mapping of refering nodes to their referents and err is an iterable
             of ValidationErrors.
    """
    sample = StringIO(sample)
    lexer = syntax.SpektakelLexer(sample)
    node = syntax.SpektakelParser.parse_block(lexer)
    return (node, *static.SpektakelValidator.validate(node, env))


class TestSpektakelValidator(unittest.TestCase):

    def assert_errors(self, expected_count, err):
        """
        Asserts that the given number of errors was found and prints an informative error message if this is not the
        case.
        :param expected_count: The number of errors expected to be found.
        :param err: An iterable of the errors that were found.
        """

        msg = "Expected {} errors, but got {}:\n{}".format(expected_count,
                                                           len(err),
                                                           "\n".join((str(e) for e in err)))
        self.assertEqual(expected_count, len(err), msg=msg)

    def assertNoErrors(self, err):
        """
        Asserts that no errors were found, or prints an informative error message.
        :param err: The errors that were found.
        """
        return self.assert_errors(0, err)

    def test_empty(self):
        """
        Tests the validator on the AST of the empty program.
        """

        env_in = static.SpektakelValidator.environment_default()
        node, env_out, dec, err = validate("# Just some empty program.", env=env_in)

        self.assertEqual(len(env_in), len(env_out))
        self.assertEqual(len(dec), 0)
        self.assertNoErrors(err)

    def test_constants(self):
        """
        Tests the validator on all sorts of constants.
        """
        env_in = static.SpektakelValidator.environment_default()

        node, env_out, dec, err = validate("True\n"
                                       "False\n"
                                       "None\n"
                                       "\"Hello world!\"\n"
                                       "\"\"\"Hello world!\"\"\"\n"
                                       "42\n"
                                       "3.1415926\n", env_in)

        self.assertEqual(len(env_in), len(env_out))
        self.assertNoErrors(err)

        found = set(dec.values())
        expected = {True, False, None, "Hello world!", 42, 3.1415926}
        self.assertSetEqual(found, expected)

    def test_identifiers(self):
        """
        Tests the correct resolution of identifiers.
        """
        env_in = static.SpektakelValidator.environment_default()

        node, env_out, dec, err = validate("x\n"
                                           "var x\n"
                                           "x = x + 42\n"
                                           "var x\n"
                                           "def x(a, b):\n"
                                           "  return x(b, a)", env_in)

        self.assertEqual(len(env_out), len(env_in) + 1)
        self.assert_errors(1, err)
        self.assertEqual(7, len(dec))

    def test_pass(self):
        """
        Makes sure that pass statements don't crash the validator.
        """
        env_in = static.SpektakelValidator.environment_default()

        node, env_out, dec, err = validate("pass", env_in)

        self.assertEqual(len(env_in), len(env_out))
        self.assertNoErrors(err)

        self.assertSetEqual(set(), set(dec.values()))

    def test_expressions(self):
        """
        Tests the the validation of some expressions
        """

        env_in = static.SpektakelValidator.environment_default()

        node, env_out, dec, err = validate("1 + 2\n"
                                           "var x = 42\n"
                                           "(await f(x)) + 42\n"
                                           "a and x > 5\n", env_in)

        self.assertEqual(len(env_out), len(env_in) + 1)
        self.assert_errors(2, err)
        self.assertEqual(7, len(dec))

    def test_assignment(self):
        """
        Tests the the validation of assignments
        """

        env_in = static.SpektakelValidator.environment_default()

        node, env_out, dec, err = validate("var x, y, z\n"
                                           "x = 42\n"
                                           "x, y = f(x)\n"
                                           "x, y = (y, x)\n", env_in)

        self.assertEqual(len(env_out), len(env_in) + 3)
        self.assert_errors(1, err)
        self.assertEqual(9, len(dec))


    def test_examples(self):
        """
        Tests the validator on all spek examples.
        """
        for path in example_paths:
            _, filename = os.path.split(path)
            with self.subTest(example=os.path.splitext(filename)[0]):
                with open(path, 'r') as sample:
                    lexer = syntax.SpektakelLexer(sample)
                    ast = syntax.SpektakelParser.parse_block(lexer)
                    env, dec, err = static.SpektakelValidator.validate(ast, Environment())
                    errs_str = ""
                    prefix = ""
                    for e in err:
                        errs_str += prefix + str(e)
                        prefix = "\n"
                    self.assertEqual(len(err), 0, msg="The validator reported unexpected errors: " + errs_str)
