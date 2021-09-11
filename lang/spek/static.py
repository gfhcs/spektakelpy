from lang.spek.ast import *
from lang.validator import *


class SpektakelValidator(Validator):
    """
    A validator for the spektakelpy default language.
    """

    def validate_expression(self):
        """ TODO:

        Expression:
            Constant
            AssignableExpression
                Identifier
                Tuple
                Projection
                Attribute
            Call
            Launch
            Await
            UnaryOperation
            BinaryOperation
                Comparison
                BooleanBinaryOperation
                ArithmeticBinaryOperation
        """
        # TODO: This thing should *not* return an environment, only a d!
        pass

    def validate_statement(self):
        """ TODO:
        Statement:
            Pass
            ExpressionStatement
            Assignment
            Block
            AtomicBlock
            Return
            Break
            Continue
            Conditional
            While
            For
            Try
            VariableDeclaration
            ProcedureDefinition
            PropertyDefinition
            ClassDefinition
        """
        pass

    @classmethod
    def validate(cls, node, env):
        """
        Validates an AST node.
        :param node: The AST node to validate.
        :param env: An Environment, mapping names to definitions.
        :return: A pair (e, d), where e is an Environment and d is dict mapping AST nodes to decorations.
        """

        if isinstance(node, Expression):
            return env, cls.validate_expression(node, env)
        elif isinstance(node, Statement):
            return cls.validate_statement(node, env)
        else:
            raise TypeError("Unknown node type: {}".format(node))

