from lang.spek.ast import *
from lang.validator import *
from enum import Enum


class ValidationKey(Enum):
    """
    Keys that identify special entries in an environment that is used for validating an AST.
    """
    LEVEL = 0
    LOOP = 1
    PROC = 2

class Level(Enum):
    """
    Denotes a level at which identifiers are being declared.
    """
    PROC = 0
    PROP = 1
    CLASS = 2
    GLOBAL = 3

class SpektakelValidator(Validator):
    """
    A validator for the spektakelpy default language.
    """

    __t2v = {"True": True, "False": False, "None": None}

    @classmethod
    def validate_expression(cls, node, env, dec=None, err=None):
        """
        Validates an Expression node.
        :param node: The Expression node to validate.
        :param env: An Environment, mapping names to definitions. This value will be modified by the procedure.
        :param dec: The mapping of nodes to decorations that should be extended.
        :param err: The list of ValidationErrors that is to be extended.
        :return: A pair (dec', err'), with the same semantics as parameters dec and err. If one of those parameters was
        given, they will be modified and returned as part of the pair.
        """

        if dec is None:
            dec = {}
        if err is None:
            err = []

        if err is None:
            err = []
        if isinstance(node, Constant):
            try:
                dec[node] = SpektakelValidator.__t2v[node.text]
            except KeyError:
                if node.text.startswith("\"\"\""):
                    dec[node] = node.text[3:-3]
                elif node.text.startswith("\""):
                    dec[node] = node.text[1:-1]
                else:
                    try:
                        dec[node] = int(node.text)
                    except ValueError:
                        try:
                            dec[node] = float(node.text)
                        except ValueError:
                            err.append(ValidationError("Invalid constant: {}".format(node.text), node))
        elif isinstance(node, Identifier):
            try:
                dec[node] = env[node.name]
            except KeyError:
                err.append(ValidationError("Name '{}' undefined!".format(node.name), node))
        elif isinstance(node, (Tuple, Projection, Attribute, Call, Launch, Await,
                               Comparison, BooleanBinaryOperation, ArithmeticBinaryOperation)):
            for c in node.children:
                cls.validate_expression(c, env, dec=dec, err=err)
        else:
            err.append(ValidationError("Invalid node type: {}".format(type(node)), node), )

        return dec, err

    @classmethod
    def _declare(cls, pattern, env):
        """
        Traverses the AST nodes of a pattern expression and adjoins the given environment.
        :param pattern: An AssignableExpression containing identifiers to be declared variables.
        :param env: The environment that is to be adjoined. It will not be modified by this method.
        :return: The new environment in which the identifiers found in the pattern are declared. Based on env.
        """
        agenda = [pattern]
        names = {}
        while len(agenda) > 0:
            node = agenda.pop()
            if isinstance(node, Identifier):
                names[node.name] = node
            else:
                agenda.extend(node.children)

        return env.adjoin(names)

    @classmethod
    def validate_statement(cls, node, env, dec=None, err=None):
        """
        Validates a Statement node.
        :param node: The Statement node to validate.
        :param env: An Environment, mapping names to definitions. It will not be modified by this procedure.
        :param dec: The mapping of nodes to decorations that should be extended.
        :param err: The list of ValidationErrors that is to be extended.
        :return: A pair (env2, dec, err), where env2 is an Environment, dec is a dict mapping AST nodes to decorations
                 and err is an iterable of ValidationError objects.
        :return: A triple (env', dec', err'), with the same semantics as parameters env, dec and err.
                 If dec or err were given, they will be modified and returned as part of the pair.
        """

        if dec is None:
            dec = {}
        if err is None:
            err = []

        if isinstance(node, Pass):
            pass
        elif isinstance(node, ExpressionStatement):
            cls.validate_expression(node.expression, env, dec=dec, err=err)
            if env[ValidationKey.Level] == Level.CLASS and not isinstance(node.expression, Constant):
                err.append(ValidationError("Expression statements in the root of a class definition must "
                                           "contain nothing other than constants!", node))
        elif isinstance(node, Assignment):
            if not isinstance(node.target, AssignableExpression):
                err.append(ValidationError("Left side of an assignment must be an assignable expression!", node.target))
            cls.validate_expression(node.target, env, dec=dec, err=err)
            cls.validate_expression(node.value, env, dec=dec, err=err)
            if env[ValidationKey.Level] == Level.CLASS:
                err.append(ValidationError("Assignments are not allowed in the root of a class definition!", node))
        elif isinstance(node, Block):
            for s in node.children:
                env, dec, err = cls.validate_statement(s, env, dec=dec, err=err)
        elif isinstance(node, Return):
            if node.value is not None:
                cls.validate_expression(node.value, env, dec=dec, err=err)
            if env[ValidationKey.PROC] is None:
                err.append(ValidationError("Return statements are only valid inside procedure bodies!", node))
            else:
                dec[node] = env[ValidationKey.PROC]
        elif isinstance(node, (Break, Continue)):
            if env[ValidationKey.LOOP] is None:
                if isinstance(node, Break):
                    t = "break"
                elif isinstance(node, Continue):
                    t = "continue"
                else:
                    raise NotImplementedError(node)
                err.append(ValidationError("{} statements are only valid inside loop bodies!".format(t), node))
            else:
                dec[node] = env[ValidationKey.LOOP]
        elif isinstance(node, Conditional):
            cls.validate_expression(node.condition, env, dec=dec, err=err)
            cls.validate_statement(node.consequence, env, dec=dec, err=err)
            cls.validate_statement(node.alternative, env, dec=dec, err=err)
            if env[ValidationKey.Level] == Level.CLASS:
                err.append(ValidationError("'if' statements are not allowed in the root of a class definition!", node))
        elif isinstance(node, While):
            cls.validate_expression(node.condition, env, dec=dec, err=err)
            cls.validate_statement(node.body, env.adjoin({ValidationKey.LOOP: node}), dec=dec, err=err)
            if env[ValidationKey.Level] == Level.CLASS:
                err.append(ValidationError("'while' statements are not allowed in the root of a class definition!", node))
        elif isinstance(node, For):
            cls.validate_expression(node.iterable, env, dec=dec, err=err)
            if not isinstance(node.pattern, AssignableExpression):
                err.append(ValidationError("The pattern must be an assignable expression!", node.pattern))
            env_body = cls._declare(node.pattern, env)
            env_body = env_body.adjoin({ValidationKey.LOOP: node})
            cls.validate_statement(node.body, env_body, dec=dec, err=err)
            if env[ValidationKey.Level] == Level.CLASS:
                err.append(ValidationError("'for' statements are not allowed in the root of a class definition!", node))
        elif isinstance(node, Try):
            cls.validate_statement(node.body, env, dec=dec, err=err)
            for h in node.handlers:
                henv = env
                if h.type is not None:
                    cls.validate_expression(h.type, env, dec=dec, err=err)
                if h.identifier is not None:
                    henv = cls._declare(h.identifier, henv)
                cls.validate_expression(h.body, henv, dec=dec, err=err)
            cls.validate_statement(node.final, env, dec=dec, err=err)
            if env[ValidationKey.Level] == Level.CLASS:
                err.append(ValidationError("'try' statements are not allowed in the root of a class definition!", node))
        elif isinstance(node, VariableDeclaration):
            if not isinstance(node.pattern, AssignableExpression):
                err.append(ValidationError("Declared expression must be assignable!", node.pattern))
            if node.expression is not None:
                cls.validate_expression(node.expression, env, dec=dec, err=err)
            env = cls._declare(node.pattern, env)
        elif isinstance(node, ProcedureDefinition):
            env = cls._declare(node.name, env)
            env_body = env
            for aname in node.argnames:
                env_body = cls._declare(aname, env_body)
            env_body = env_body.adjoin({ValidationKey.LEVEL: Level.PROC, ValidationKey.PROC: node})
            cls.validate_statement(node.body, env_body, dec=dec, err=err)
        elif isinstance(node, PropertyDefinition):
            if env[ValidationKey.LEVEL != Level.CLASS]:
                err.append(ValidationError("Property definitions are only allowed as directly members of a class definition!", node))
            genv = env
            genv = genv.adjoin({ValidationKey.LEVEL: Level.PROP})
            cls.validate_statement(node.getter, genv, dec=dec, err=err)
            senv = cls._declare(node.vname, env)
            senv = senv.adjoin({ValidationKey.LEVEL: Level.PROP})
            cls.validate_statement(node.body, senv, dec=dec, err=err)
            env = cls._declare(node.name, env)
        elif isinstance(node, ClassDefinition):
            if env[ValidationKey.LEVEL != Level.GLOBAL]:
                err.append(ValidationError("Class definitions are only allowed on the global level!", node))
            for b in node.bases:
                cls.validate_expression(b, env, dec=dec, err=err)
            env = cls._declare(node.name, env)
            ebody = env({ValidationKey.LEVEL: Level.CLASS, "self": node})
            cls.validate_statement(node.body, ebody, dec=dec, err=err)
        else:
            err.append(ValidationError("Invalid statement type: {}".format(type(node)), node))

        return env, dec, err

    @classmethod
    def validate(cls, node, env):
        if isinstance(node, Expression):
            return (env, *(cls.validate_expression(node, env)))
        elif isinstance(node, Statement):
            return cls.validate_statement(node, env)
        else:
            raise TypeError("Unknown node type: {}".format(node))

