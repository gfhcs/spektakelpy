from lang.translator import Translator
from .ast import Pass, Constant, Identifier, Attribute, Tuple, Projection, Call, Launch, Await, Comparison, \
    BooleanBinaryOperation, UnaryOperation, ArithmeticBinaryOperation, ImportNames, ImportSource, \
    ExpressionStatement, Assignment, Block, Return, Raise, Break, \
    Continue, Conditional, While, For, Try, VariableDeclaration, ProcedureDefinition, \
    PropertyDefinition, ClassDefinition

class Spektakel2Stack(Translator):
    """
    A translator that translates Spektakel AST nodes into stack programs.
    """

    def translate_expression(self, node, dec):
        """
        Translates an AST expression into a machine expression.
        :param node: An AST node representing an expression.
        :param dec: A dict mapping AST nodes to decorations.
        :return: A machine Expression object.
        """

        if isinstance(node, Constant):

        elif isinstance(node, Identifier):

        elif isinstance(node, Attribute):

        elif isinstance(node, (Tuple, Projection, Call, Launch, Await,
                               Comparison, BooleanBinaryOperation, UnaryOperation, ArithmeticBinaryOperation)):

        else:
            raise NotImplementedError()

    def translate_statement(self, node, dec):
        """
        Translates a statement into a StackProgram.
        :param node: An AST node representing a Statement.
        :param dec: A dict mapping AST nodes to decorations.
        :return: A StackProgram.
        """

        if isinstance(node, Pass):
            pass
        elif isinstance(node, (ImportNames, ImportSource)):

        elif isinstance(node, ExpressionStatement):
        elif isinstance(node, Assignment):

        elif isinstance(node, Block):

        elif isinstance(node, Return):

        elif isinstance(node, Raise):

        elif isinstance(node, (Break, Continue)):

        elif isinstance(node, Conditional):

        elif isinstance(node, While):

        elif isinstance(node, For):

        elif isinstance(node, Try):

        elif isinstance(node, VariableDeclaration):

        elif isinstance(node, ProcedureDefinition):

        elif isinstance(node, PropertyDefinition):

        elif isinstance(node, ClassDefinition):

        else:
            raise NotImplementedError()


    def translate(self, node, dec):
        pass

