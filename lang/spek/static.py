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

        if isinstance(node, Pass):
            return env, {}, []
        elif isinstance(node, ExpressionStatement):
            # TODO: Unless we are *in* a procedure/property or *outside* of a class definition, only expressions without
            #       any side effects are allowed, which must be syntactically clear!
            return (env, *cls.validate_expression(node.expression, env))
        elif isinstance(node, Assignment):
            # TODO: Not allowed in a class.
            # TODO: Left hand side must be assignable
            # TODO: Left hand and right hand side must be valid
        elif isinstance(node, Block):
            dec = {}
            err = []
            for s in node.children:
                env, sdec, serr = cls.validate_statement(s, env)
                dec.update(sdec)
                err.extend(serr)
            return env, dec, err
        elif isinstance(node, Return):
            # TODO: Expression must be valid.
            # TODO: Must decorate this node with the procedure it is contained in. Error if there is no such procedure!
        elif isinstance(node, (Break, Continue)):
            # TODO: Must decorate with enclosing loop, error if there is none.
        elif isinstance(node, Conditional):
            # TODO: Conditions must be valid.
            # TODO: Blocks must be validated, but the resulting environment is the INPUT ENVIRONMENT, UNMODIFIED!
        elif isinstance(node, While):
            # TODO: Condition must be valid.
            # TODO: Body must be validated, but the resulting environment is the INPUT ENVIRONMENT, UNMODIFIED!
        elif isinstance(node, For):
            # TODO: Iterable must be valid.
            # TODO: Pattern must be assignable, but declares its names shadowingly!
            # TODO: Body must be validated, but the resulting environment is the INPUT ENVIRONMENT, UNMODIFIED!
        elif isinstance(node, Try):
            # TODO: Block must be valid.
            # TODO: Finally-Block must be valid.
            # TODO: Except clauses must be valid.
            # TODO: Resulting environment is the INPUT ENVIRONMENT, UNMODIFIED!
        elif isinstance(node, VariableDeclaration):
            # TODO: If there is an assigned expression, it must be valid!
            # TODO: Updates the environment!
            # TODO: Allowed everywhere.
        elif isinstance(node, ProcedureDefinition):
            # TODO: Declares the name of the procedure.
            # TODO: Args are declared for the body.
            # TODO: Body must be valid.
        elif isinstance(node, PropertyDefinition):
            # TODO: Only allowed in a class.
            # TODO: Otherwise most things from procedures carry over.
        elif isinstance(node, ClassDefinition):
            # TODO: Allowed only on the top level.
            # TODO: Should make 'self' available in enclosed procedures and properties.
            # TODO: Declares class name.
            # TODO: Validate super class names!
        else:
            return env, {}, (ValidationError("Invalid statement type: {}".format(type(node)), node), )


    @classmethod
    def validate(cls, node, env):
        if isinstance(node, Expression):
            return (env, *(cls.validate_expression(node, env)))
        elif isinstance(node, Statement):
            return cls.validate_statement(node, env)
        else:
            raise TypeError("Unknown node type: {}".format(node))

