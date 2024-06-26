from enum import Enum

from lang.modules import Finder
from lang.spek.ast import Identifier, Tuple, Constant, Attribute, Projection, Call, Await, Launch, \
    ArithmeticBinaryOperation, UnaryOperation, Comparison, BooleanBinaryOperation, VariableDeclaration, Assignment, \
    ExpressionStatement, Return, Raise, Continue, Break, Pass, Block, Conditional, ImportSource, ImportNames, \
    While, For, Try, PropertyDefinition, ProcedureDefinition, ClassDefinition, List, Dict, Expression, Statement
from lang.spek.modules import BuiltinModuleSpecification
from lang.validator import Validator, ValidationError
from util import check_type
from util.environment import Environment


class ValidationKey(Enum):
    """
    Keys that identify special entries in an environment that is used for validating an AST.
    """
    LEVEL = 0
    LOOP = 1
    PROC = 2
    EXCEPT = 4


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

    def __init__(self, finder, builtin):
        """
        Initializes a new Spektakel validator.
        :param finder: A Finder that is used to resolve module imports.
        :param builtin: An iterable of BuiltinModuleSpecification objects that define identifiers that are to be
                        builtin, i.e. valid without any explicit definition or import.
        """
        
        if not isinstance(finder, Finder):
            raise TypeError("'finder' must be a Finder object!")
        
        super().__init__()

        self._finder = finder
        self.__t2v = {"True": True, "False": False, "None": None}

        self._denv = {ValidationKey.LEVEL: Level.GLOBAL, ValidationKey.LOOP: None, ValidationKey.EXCEPT: None, ValidationKey.PROC: None}
        for b in builtin:
            check_type(b, BuiltinModuleSpecification)
            for s in b.symbols:
                self._denv[s] = (b, s)

        self._denv = Environment(k2v=self._denv)
        self._builtin = builtin

    @property
    def finder(self):
        """
        The Finder that is used to resolve module imports.
        """
        return self._finder

    @property
    def environment_default(self):
        """
        The environment that a program is validated in by default.
        :return: An Environment object.
        """
        return self._denv

    def validate_expression(self, node, env=None, dec=None, err=None, mspec=None):
        """
        Validates an Expression node.
        :param node: The Expression node to validate.
        :param env: An Environment, mapping names to definitions. This value will be modified by the procedure.
        :param dec: The mapping of nodes to decorations that should be extended.
        :param err: The list of ValidationErrors that is to be extended.
        :param mspec: The ModuleSpecification object that yielded the given 'node'.
        :return: A pair (dec', err'), with the same semantics as parameters dec and err. If one of those parameters was
        given, they will be modified and returned as part of the pair.
        """

        if dec is None:
            dec = {}
        if err is None:
            err = []
        if env is None:
            env = self.environment_default

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
                            err.append(ValidationError("Invalid constant: {}".format(node.text), node, mspec))
        elif isinstance(node, Identifier):
            try:
                dec[node] = env[node.name]
            except KeyError:
                err.append(ValidationError("Name '{}' undefined!".format(node.name), node, mspec))
        elif isinstance(node, Attribute):

            # An Attribute expression could refer to an imported module name (containing dots).
            # In that case we want to bind the name to the defining import statement.

            # Step 1: Recurse into the left hand side of the dot, to find out if we might be looking at syntactically
            # valid module name:
            names = []
            n = node
            while isinstance(n, Attribute):
                names.insert(0, (n, n.name.name))
                n = n.value
            if isinstance(n, Identifier):  # There would need to be an identifier on the very left for this expression
                                           # to refer to a module.
                # We want to bind a maximal prefix:
                names.insert(0, (n, n.name))
                while len(names) > 0:
                    try:
                        dec[names[-1][0]] = env[".".join(name for _, name in names)]
                        break
                    except KeyError:
                        names.pop()
                # If the maximal prefix is empty, then we are not looking at an imported module name.
                # In this case we simply validate the leftmost identifier:
                if len(names) == 0:
                    self.validate_expression(n, env, dec=dec, err=err, mspec=mspec)
            else:
                self.validate_expression(node.value, env, dec=dec, err=err, mspec=mspec)
        elif isinstance(node, (Tuple, List, Dict, Projection, Call, Launch, Await,
                               Comparison, BooleanBinaryOperation, UnaryOperation, ArithmeticBinaryOperation)):
            for c in node.children:
                self.validate_expression(c, env, dec=dec, err=err, mspec=mspec)
        else:
            err.append(ValidationError("Invalid node type: {}".format(type(node)), node, mspec))

        return dec, err

    @staticmethod
    def _declare(decl, pattern, env):
        """
        Traverses the AST nodes of a pattern expression and adjoins the given environment.
        :param decl: The node that represents the declaration.
        :param pattern: An Expression containing identifiers to be declared variables, or a string.
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

    def validate_statement(self, node, env=None, dec=None, err=None, mspec=None):
        """
        Validates a Statement node.
        :param node: The Statement node to validate.
        :param env: An Environment, mapping names to definitions. It will not be modified by this procedure.
        :param dec: The mapping of nodes to decorations that should be extended.
        :param err: The list of ValidationErrors that is to be extended.
        :param mspec: The ModuleSpecification object that yielded the given 'node'.
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
            env = self.environment_default

        if isinstance(node, Pass):
            pass
        elif isinstance(node, (ImportNames, ImportSource)):

            key = tuple(i.name for i in node.source.identifiers)

            try:
                spec = self._finder.find(key, self, self._builtin)
                dec[node.source] = spec
            except KeyError:
                err.append(ValidationError("The module name '{}' could not be resolved!".format(".".join(key)), node.source, mspec))

            if isinstance(node, ImportSource):
                alias = ".".join(i.name for i in node.source.identifiers) if node.alias is None else node.alias
                env = self._declare(node, alias, env)
            elif isinstance(node, ImportNames):

                if node.wildcard:
                    raise RuntimeError("The validator does not support wildcards, because it would have to recurse"
                                       "into the imported module for that.")
                else:
                    for name, alias in node.aliases.items():
                        try:
                            env = self._declare(node, alias, env)
                            if alias is not name:
                                dec[alias] = name
                        except KeyError:
                            err.append(ValidationError("Module {} does not contain a definition for name {}!".format(".".join(key), name.name), name, mspec))
            else:
                raise NotImplementedError("Handling import nodes of type {}"
                                          " has not been implemented!".format(type(node)))
        elif isinstance(node, ExpressionStatement):
            if env[ValidationKey.LEVEL] == Level.CLASS and not isinstance(node.expression, Constant):
                err.append(ValidationError("Expression statements in the root of a class definition must "
                                           "contain nothing other than constants!", node, mspec))
            else:
                self.validate_expression(node.expression, env, dec=dec, err=err, mspec=mspec)
        elif isinstance(node, Assignment):
            if not node.target.assignable:
                err.append(ValidationError("Left side of an assignment must be an assignable expression!", node.target, mspec))
            self.validate_expression(node.target, env, dec=dec, err=err, mspec=mspec)
            self.validate_expression(node.value, env, dec=dec, err=err, mspec=mspec)
            if env[ValidationKey.LEVEL] == Level.CLASS:
                err.append(ValidationError("Assignments are not allowed in the root of a class definition!", node, mspec))
        elif isinstance(node, Block):
            for s in node.children:
                env, dec, err = self.validate_statement(s, env, dec=dec, err=err, mspec=mspec)
        elif isinstance(node, Return):
            if node.value is not None:
                self.validate_expression(node.value, env, dec=dec, err=err, mspec=mspec)
            if env[ValidationKey.PROC] is None:
                err.append(ValidationError("'return' statements are only valid inside procedure bodies!", node, mspec))
            else:
                dec[node] = env[ValidationKey.PROC]
        elif isinstance(node, Raise):
            if node.value is None:
                if env[ValidationKey.EXCEPT] is None:
                    err.append(ValidationError(f"'raise' statements without an exception are only valid inside except clauses!", node, mspec))
            else:
                self.validate_expression(node.value, env, dec=dec, err=err, mspec=mspec)
        elif isinstance(node, (Break, Continue)):
            if env[ValidationKey.LOOP] is None:
                if isinstance(node, Break):
                    t = "break"
                elif isinstance(node, Continue):
                    t = "continue"
                else:
                    raise NotImplementedError(node)
                err.append(ValidationError("{} statements are only valid inside loop bodies!".format(t), node, mspec))
            else:
                dec[node] = env[ValidationKey.LOOP]
        elif isinstance(node, Conditional):
            self.validate_expression(node.condition, env, dec=dec, err=err, mspec=mspec)
            self.validate_statement(node.consequence, env, dec=dec, err=err, mspec=mspec)
            if node.alternative is not None:
                self.validate_statement(node.alternative, env, dec=dec, err=err, mspec=mspec)
            if env[ValidationKey.LEVEL] == Level.CLASS:
                err.append(ValidationError("'if' statements are not allowed in the root of a class definition!", node, mspec))
        elif isinstance(node, While):
            self.validate_expression(node.condition, env, dec=dec, err=err, mspec=mspec)
            self.validate_statement(node.body, env.adjoin({ValidationKey.LOOP: node}), dec=dec, err=err, mspec=mspec)
            if env[ValidationKey.LEVEL] == Level.CLASS:
                err.append(ValidationError("'while' statements are not allowed in the root of a class definition!", node, mspec))
        elif isinstance(node, For):
            self.validate_expression(node.iterable, env, dec=dec, err=err, mspec=mspec)
            if not node.pattern.assignable:
                err.append(ValidationError("The pattern must be an assignable expression!", node.pattern, mspec))
            env_body = self._declare(node, node.pattern, env)
            env_body = env_body.adjoin({ValidationKey.LOOP: node})
            self.validate_statement(node.body, env_body, dec=dec, err=err, mspec=mspec)
            if env[ValidationKey.LEVEL] == Level.CLASS:
                err.append(ValidationError("'for' statements are not allowed in the root of a class definition!", node, mspec))
        elif isinstance(node, Try):
            self.validate_statement(node.body, env, dec=dec, err=err, mspec=mspec)
            for h in node.handlers:
                henv = env
                if h.type is not None:
                    self.validate_expression(h.type, env, dec=dec, err=err, mspec=mspec)
                if h.identifier is not None:
                    henv = self._declare(h, h.identifier, henv)
                self.validate_statement(h.body, henv.adjoin({ValidationKey.EXCEPT: node}), dec=dec, err=err, mspec=mspec)
            if node.final is not None:
                self.validate_statement(node.final, env, dec=dec, err=err, mspec=mspec)
            if env[ValidationKey.LEVEL] == Level.CLASS:
                err.append(ValidationError("'try' statements are not allowed in the root of a class definition!", node, mspec))
        elif isinstance(node, VariableDeclaration):
            if not node.pattern.assignable:
                err.append(ValidationError("Declared expression must be assignable!", node.pattern, mspec))
            if node.expression is not None:
                self.validate_expression(node.expression, env, dec=dec, err=err, mspec=mspec)
            env = self._declare(node, node.pattern, env)
        elif isinstance(node, ProcedureDefinition):
            if env[ValidationKey.LEVEL] == Level.CLASS:
                if len(node.argnames) < 1:
                    err.append(ValidationError("Instance method must take at least one argument (the instance)!", node, mspec))
            env = self._declare(node, node.name, env)
            env_body = env
            anames = set()
            for aname in node.argnames:
                env_body = self._declare(node, aname, env_body)
                for n in env_body.direct.keys():
                    if n in anames:
                        err.append(ValidationError("Duplicate argument '{}' in procedure declaration!".format(n), aname, mspec))
                    anames.add(n)
            env_body = env_body.adjoin({ValidationKey.LEVEL: Level.PROC, ValidationKey.PROC: node})
            self.validate_statement(node.body, env_body, dec=dec, err=err, mspec=mspec)
        elif isinstance(node, PropertyDefinition):
            genv = self._declare(node.gself, node.gself, env)
            genv = genv.adjoin({ValidationKey.LEVEL: Level.PROP, ValidationKey.PROC: node})
            self.validate_statement(node.getter, genv, dec=dec, err=err, mspec=mspec)
            senv = self._declare(node.sself, node.sself, env)
            senv = self._declare(node.vname, node.vname, senv)
            senv = senv.adjoin({ValidationKey.LEVEL: Level.PROP, ValidationKey.PROC: node})
            self.validate_statement(node.setter, senv, dec=dec, err=err, mspec=mspec)
            if env[ValidationKey.LEVEL] != Level.CLASS:
                err.append(ValidationError("Property definitions are only allowed as direct members of a class definition!", node, mspec))
            env = self._declare(node, node.name, env)
        elif isinstance(node, ClassDefinition):
            for b in node.bases:
                self.validate_expression(b, env, dec=dec, err=err, mspec=mspec)
            env = self._declare(node, node.name, env)
            ebody = env.adjoin({ValidationKey.LEVEL: Level.CLASS})
            members = {}
            for d in node.body.children:
                if isinstance(d, (VariableDeclaration, PropertyDefinition, ProcedureDefinition)):
                    if isinstance(d, VariableDeclaration) and d.expression is not None:
                        err.append(ValidationError("Field declarations must not initialize fields!", d, mspec))
                    env_after, dec, err = self.validate_statement(d, ebody, dec=dec, err=err, mspec=mspec)
                    assert env_after is not ebody
                    for k, v in env_after.direct.items():
                        if k in members:
                            err.append(ValidationError("A member with the name {} has already been declared!".format(k), d, mspec))
                        members[k] = v
                elif isinstance(d, (Pass, ExpressionStatement)):
                    _, dec, err = self.validate_statement(d, ebody, dec=dec, err=err, mspec=mspec)
                else:
                    err.append(ValidationError("Invalid statement type inside class declaration!", d, mspec))
            dec[node] = members
        else:
            err.append(ValidationError("Invalid statement type: {}".format(type(node)), node, mspec))

        return env, dec, err

    def validate(self, node, env=None, mspec=None):
        if isinstance(node, Expression):
            return (env, *(self.validate_expression(node, env, mspec=mspec)))
        elif isinstance(node, Statement):
            return self.validate_statement(node, env, mspec=mspec)
        else:
            raise TypeError("Unknown node type: {}".format(node))

