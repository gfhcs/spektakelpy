import os.path
import unittest

from examples import paths as example_paths
from lang.environment import Environment
from lang.spek import syntax, static


class TestSpektakelValidator(unittest.TestCase):

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
