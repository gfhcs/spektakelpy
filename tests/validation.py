import os.path
import unittest

from examples import paths as example_paths
from lang.environment import Environment
from lang.spek import syntax, static
from io import StringIO


def validate(sample, env=Environment()):
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

    def assertNoErrors(self, err):
        errs_str = ""
        prefix = ""
        for e in err:
            errs_str += prefix + str(e)
            prefix = "\n"
        self.assertEqual(len(err), 0, msg="The validator reported unexpected errors: " + errs_str)

    def test_empty(self):
        """
        Tests the validator on the AST of the empty program.
        """

        node, env, dec, err = validate("# Just some empty program.")

        self.assertEqual(len(env), 0)
        self.assertEqual(len(dec), 0)
        self.assertNoErrors(err)

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
