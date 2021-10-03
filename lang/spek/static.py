from lang.environment import Environment
from lang.modules import Finder
from lang.validator import *


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
    A validator for the Spektakel language.
    """

    __env = Environment({ValidationKey.LEVEL: Level.GLOBAL, ValidationKey.LOOP: None, ValidationKey.PROC: None})

    def __init__(self, finder):
        """
        Initializes a new Spektakel validator.
        :param finder: A Finder that is used to resolve module imports.
        """
        
        if not isinstance(finder, Finder):
            raise TypeError("'finder' must be a Finder object!")
        
        super().__init__()

        self._finder = finder
        self.__t2v = {"True": True, "False": False, "None": None}

    @property
    def finder(self):
        """
        The Finder that is used to resolve module imports.
        """
        return self._finder

    @classmethod
    def environment_default(cls):
        """
        The environment that a program is validated in by default.
        :return: An Environment object.
        """
        return cls.__env

    def validate_expression(self, node, env=None, dec=None, err=None):
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
        if env is None:
            env = self.environment_default()

        if err is None:
            err = []
        if isinstance(node, Constant):
            try:
                dec[node] = self.__t2v[node.text]
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
        elif isinstance(node, Attribute):
            self.validate_expression(node.value, env, dec=dec, err=err)
        elif isinstance(node, (Tuple, Projection, Call, Launch, Await,
                               Comparison, BooleanBinaryOperation, UnaryOperation, ArithmeticBinaryOperation)):
            for c in node.children:
                self.validate_expression(c, env, dec=dec, err=err)
        else:
            err.append(ValidationError("Invalid node type: {}".format(type(node)), node), )

        return dec, err

    @staticmethod
    def _declare(decl, pattern, env):
        """
        Traverses the AST nodes of a pattern expression and adjoins the given environment.
        :param decl: The node that represents the declaration.
        :param pattern: An AssignableExpression containing identifiers to be declared variables, or a string.
        :param env: The environment that is to be adjoined. It will not be modified by this method.
        :return: The new environment in which the identifiers found in the pattern are declared. Based on env.
        """
        agenda = [pattern]
        names = {}
        while len(agenda) > 0:
            node = agenda.pop()
            if isinstance(node, str):
                names[node] = (decl, node)
            elif isinstance(node, Identifier):
                names[node.name] = (decl, node)
            else:
                agenda.extend(node.children)

        return env.adjoin(names)

    def validate_statement(self, node, env=None, dec=None, err=None):
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
        if env is None:
            env = self.environment_default()

        if isinstance(node, Pass):
            pass
        elif isinstance(node, (ImportNames, ImportSource)):

            key = tuple(i.name for i in node.source.identifiers)

            try:
                spec = self._finder.find(key, validator=self)
            except KeyError:
                err.append(ValidationError("The module name '{}' could not be resolved!".format(".".join(key)), node.source))
                spec = None

            module = None
            if spec is not None:
                try:
                    module = spec.load()
                except Exception as ex:
                    err.append(ValidationError("Failed to load module {}: {}".format(".".join(key), str(ex)), node.source))

            if module is not None:
                dec[node.source] = module

            if isinstance(node, ImportSource):
                if node.alias is None:
                    # The first element of the key is considered declared now. The following items
                    # are attributes of the first, which the validator does not care about:
                    env = self._declare(node, node.source.identifiers[0], env)
                else:
                    env = self._declare(node, node.alias, env)
            elif isinstance(node, ImportNames):
                if node.wildcard:
                    bindings = ((name, definition) for name, definition in module)
                else:
                    bindings = []
                    for name, alias in node.aliases.items():
                        try:
                            bindings.append((alias, module[name.name]))
                        except KeyError:
                            err.append(ValidationError("Module {} does not contain a definition for name {}!".format(".".join(key), name.name)))
                            bindings.append((alias, None))

                for alias, definition in bindings:
                    env = self._declare(node, alias, env)
                    dec[alias] = definition
            else:
                raise NotImplementedError("Handling import nodes of type {}"
                                          " has not been implemented!".format(type(node)))
        elif isinstance(node, ExpressionStatement):
            if env[ValidationKey.LEVEL] == Level.CLASS and not isinstance(node.expression, Constant):
                err.append(ValidationError("Expression statements in the root of a class definition must "
                                           "contain nothing other than constants!", node))
            else:
                self.validate_expression(node.expression, env, dec=dec, err=err)
        elif isinstance(node, Assignment):
            if not isinstance(node.target, AssignableExpression):
                err.append(ValidationError("Left side of an assignment must be an assignable expression!", node.target))
            self.validate_expression(node.target, env, dec=dec, err=err)
            self.validate_expression(node.value, env, dec=dec, err=err)
            if env[ValidationKey.LEVEL] == Level.CLASS:
                err.append(ValidationError("Assignments are not allowed in the root of a class definition!", node))
        elif isinstance(node, Block):
            for s in node.children:
                env, dec, err = self.validate_statement(s, env, dec=dec, err=err)
        elif isinstance(node, Return):
            if node.value is not None:
                self.validate_expression(node.value, env, dec=dec, err=err)
            if env[ValidationKey.PROC] is None:
                err.append(ValidationError("'return' statements are only valid inside procedure bodies!", node))
            else:
                dec[node] = env[ValidationKey.PROC]
        elif isinstance(node, Raise):
            if node.value is not None:
                self.validate_expression(node.value, env, dec=dec, err=err)
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
            self.validate_expression(node.condition, env, dec=dec, err=err)
            self.validate_statement(node.consequence, env, dec=dec, err=err)
            if node.alternative is not None:
                self.validate_statement(node.alternative, env, dec=dec, err=err)
            if env[ValidationKey.LEVEL] == Level.CLASS:
                err.append(ValidationError("'if' statements are not allowed in the root of a class definition!", node))
        elif isinstance(node, While):
            self.validate_expression(node.condition, env, dec=dec, err=err)
            self.validate_statement(node.body, env.adjoin({ValidationKey.LOOP: node}), dec=dec, err=err)
            if env[ValidationKey.LEVEL] == Level.CLASS:
                err.append(ValidationError("'while' statements are not allowed in the root of a class definition!", node))
        elif isinstance(node, For):
            self.validate_expression(node.iterable, env, dec=dec, err=err)
            if not isinstance(node.pattern, AssignableExpression):
                err.append(ValidationError("The pattern must be an assignable expression!", node.pattern))
            env_body = self._declare(node, node.pattern, env)
            env_body = env_body.adjoin({ValidationKey.LOOP: node})
            self.validate_statement(node.body, env_body, dec=dec, err=err)
            if env[ValidationKey.LEVEL] == Level.CLASS:
                err.append(ValidationError("'for' statements are not allowed in the root of a class definition!", node))
        elif isinstance(node, Try):
            self.validate_statement(node.body, env, dec=dec, err=err)
            for h in node.handlers:
                henv = env
                if h.type is not None:
                    self.validate_expression(h.type, env, dec=dec, err=err)
                if h.identifier is not None:
                    henv = self._declare(h, h.identifier, henv)
                self.validate_statement(h.body, henv, dec=dec, err=err)
            if node.final is not None:
                self.validate_statement(node.final, env, dec=dec, err=err)
            if env[ValidationKey.LEVEL] == Level.CLASS:
                err.append(ValidationError("'try' statements are not allowed in the root of a class definition!", node))
        elif isinstance(node, VariableDeclaration):
            if not isinstance(node.pattern, AssignableExpression):
                err.append(ValidationError("Declared expression must be assignable!", node.pattern))
            if node.expression is not None:
                self.validate_expression(node.expression, env, dec=dec, err=err)
            env = self._declare(node, node.pattern, env)
        elif isinstance(node, ProcedureDefinition):
            env = self._declare(node, node.name, env)
            env_body = env
            anames = set()
            for aname in node.argnames:
                env_body = self._declare(node, aname, env_body)
                for n in env_body.direct.keys():
                    if n in anames:
                        err.append(ValidationError("Duplicate argument '{}' in procedure declaration!".format(n), aname))
                    anames.add(n)
            env_body = env_body.adjoin({ValidationKey.LEVEL: Level.PROC, ValidationKey.PROC: node})
            self.validate_statement(node.body, env_body, dec=dec, err=err)
        elif isinstance(node, PropertyDefinition):
            genv = env
            genv = genv.adjoin({ValidationKey.LEVEL: Level.PROP, ValidationKey.PROC: node})
            self.validate_statement(node.getter, genv, dec=dec, err=err)
            senv = self._declare(node, node.vname, env)
            senv = senv.adjoin({ValidationKey.LEVEL: Level.PROP, ValidationKey.PROC: node})
            self.validate_statement(node.setter, senv, dec=dec, err=err)
            if env[ValidationKey.LEVEL] != Level.CLASS:
                err.append(ValidationError("Property definitions are only allowed as direct members of a class definition!", node))
            env = self._declare(node, node.name, env)
        elif isinstance(node, ClassDefinition):
            if env[ValidationKey.LEVEL] != Level.GLOBAL:
                err.append(ValidationError("Class definitions are only allowed on the global level!", node))
            for b in node.bases:
                self.validate_expression(b, env, dec=dec, err=err)
            env = self._declare(node, node.name, env)
            ebody = env.adjoin({ValidationKey.LEVEL: Level.CLASS, "self": node})
            members = {}
            for d in node.body.children:
                if isinstance(d, (VariableDeclaration, PropertyDefinition, ProcedureDefinition)):
                    env_after, dec, err = self.validate_statement(d, ebody, dec=dec, err=err)
                    assert env_after is not ebody
                    for k, v in env_after.direct.items():
                        if k in members:
                            err.append(ValidationError("A member with the name {} has already been declared!".format(k), d))
                        members[k] = v
                elif isinstance(d, (Pass, ExpressionStatement)):
                    _, dec, err = self.validate_statement(d, ebody, dec=dec, err=err)
                else:
                    err.append(ValidationError("Invalid statement type inside class declaration!", d))
            dec[node] = members
        else:
            err.append(ValidationError("Invalid statement type: {}".format(type(node)), node))

        return env, dec, err

    def validate(self, node, env=None):
        if isinstance(node, Expression):
            return (env, *(self.validate_expression(node, env)))
        elif isinstance(node, Statement):
            return self.validate_statement(node, env)
        else:
            raise TypeError("Unknown node type: {}".format(node))

