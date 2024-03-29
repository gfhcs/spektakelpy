import unittest

from lang.spek import static, modules
from lang.spek.data.terms import ComparisonOperator, Comparison, UnaryOperator, UnaryOperation, CNone, \
    BooleanBinaryOperation, BooleanBinaryOperator, CBool
from lang.spek.dynamic import Spektakel2Stack
from lang.spek.modules import SpekStringModuleSpecification


class TestPrinting(unittest.TestCase):
    """
    This class is for testing the Printable implementations related to compiled programs.
    """

    def compile(self, sample, env=None, roots=None):
        """
        Translates and the given code sample to VM code.
        :param env: The environment in which the AST of the given sample is to be validated.
        :exception ParserError: If the given string was not a syntactically correct Spektakel program.
        :param sample: The code to lex, parse and validate, as a string.
        :param roots: The file system roots that should be searched for modules to be imported.
        :return: A StackProgram object.
        """
        finder, builtin = modules.build_default_finder([] if roots is None else roots)
        v = static.SpektakelValidator(finder, builtin)

        translator = Spektakel2Stack(builtin)

        program = translator.translate(SpekStringModuleSpecification(sample, v, builtin))

        program = program.compile()

        return program

    def test_empty(self):
        """
        Tests if the machine for the empty program can be printed without crash.
        """
        program = self.compile("# Just some empty program.")
        str(program)

    def test_negated_comparison(self):
        """
        Tests that the printing for a negated comparison does _not_ put the comparison into parentheses
        and that 'not' is used to print negations.
        """
        term = UnaryOperation(UnaryOperator.NOT, Comparison(ComparisonOperator.EQ, CNone(), CNone()))

        s = str(term)

        self.assertTrue(s.count("(") <= 2 and s.count("(") <= 2)

        self.assertTrue("not" in s)

    def test_and(self):
        """
        Tests that pretty-printing AND expressions works.
        """

        term = BooleanBinaryOperation(BooleanBinaryOperator.AND, CBool(True), CBool(True))

        self.assertEqual("True and True", str(term))
