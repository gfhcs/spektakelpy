from lang.spek.ast import *
from lang.validator import *


class SpektakelValidator(Validator):
    """
    A validator for the spektakelpy default language.
    """

    @classmethod
    def _validate_constant(cls, node):
        """
        Validates a Constant node.
        :param node: The Constant node to validate.
        :return: A pair (d, err), where d is a dict mapping sub-nodes of this node to decorations
                and err is an iterable of errors.
        """
        if node.text == "True":
            return {node: True}, ()
        elif node.text == "False":
            return {node: False}, ()
        elif node.text == "None":
            return {node: None}, ()
        elif node.text.startswith("\"\"\""):
            return {node: node.text[3:-3]}, ()
        elif node.text.startswith("\""):
            return {node: node.text[1:-1]}, ()
        else:
            try:
                return {node: int(node.text)}, ()
            except ValueError:
                try:
                    return {node: float(node.text)}, ()
                except ValueError:
                    return {}, (ValidationError("Invalid constant: {}".format(node.text), node))

    @classmethod
    def _validate_identifier(cls, node, env):
        """
        Validates an Identifier node.
        :param node: The Identifier node to validate.
        :param env: An Environment, mapping names to definitions.
        :return: A pair (d, err), where d is a dict mapping sub-nodes of this node to decorations
                and err is an iterable of errors.
        """
        name = Identifier.name
        try:
            definition = env[name]
        except KeyError:
            return {}, ValidationError("Name '{}' undefined!".format(name), node)

        return {node: definition}, ()

    @classmethod
    def validate_expression(cls, node, env):
        """
        Validates an Expression node.
        :param node: The Expression node to validate.
        :param env: An Environment, mapping names to definitions.
        :return: A pair (d, err), where d is a dict mapping sub-nodes of this node to decorations
                and err is an iterable of errors.
        """

        if isinstance(node, Constant):
            return cls._validate_constant(node)
        elif isinstance(node, Identifier):
            return cls._validate_identifier(node, env)
        elif isinstance(node, (Tuple, Projection, Attribute, Call, Launch, Await,
                               Comparison, BooleanBinaryOperation, ArithmeticBinaryOperation)):
            d = {}
            err = []
            for c in node.children:
                cd, cerr = cls.validate_expression(c, env)
                d.update(cd)
                err.extend(cerr)
            return d, err
        else:
            return {}, (ValidationError("Invalid node type: {}".format(type(node)), node), )

    @classmethod
    def validate_statement(cls, node, env):
        """
        Validates a Statement node.
        :param node: The Statement node to validate.
        :param env: An Environment, mapping names to definitions.
        :return: A pair (env2, dec, err), where env2 is an Environment, dec is a dict mapping AST nodes to decorations
                 and err is an iterable of ValidationError objects.
        """

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
        if isinstance(node, Expression):
            return (env, *(cls.validate_expression(node, env)))
        elif isinstance(node, Statement):
            return cls.validate_statement(node, env)
        else:
            raise TypeError("Unknown node type: {}".format(node))

