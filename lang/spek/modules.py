import abc

from lang.modules import Module, ModuleSpecificaion
from lang.validator import ValidationError
from lang.spek.syntax import SpektakelLexer, SpektakelParser


class ASTSpecification(ModuleSpecificaion, abc.ABC):
    """
    Specifies that ASTModule is to be loaded.
    """

    def __init__(self, validator):
        """
        Creates the specification for a module that is defined by an AST.
        :param validator: The validator to be used for validating the AST defining this module.
        """
        super().__init__()
        self._validator = validator
        self._loading = False
        self._module = None

    @abc.abstractmethod
    def load_ast(self):
        """
        Loads the abstract syntax tree defining the contents of this module.
        """
        pass

    def load(self):
        if self._module is None:
            if self._loading:
                raise ValidationError("The loading of this module seems to depend on loading this module, "
                                      "i.e. there is a circular dependency somewhere!")
            try:
                self._loading = True
                ast = self.load_ast()
                env, dec, err = self._validator.validate(ast)
                self._module = ASTModule(ast, env, dec, err)
            finally:
                self._loading = False
        return self._module


class SpekFileSpecification(ASTSpecification):
    """
    Specifies a module that is to be loaded from a *.spek file on disk.
    """

    def __init__(self, path, validator):
        """
        Creates the specification for a module that is to be loaded from a *.spek file.
        :param path: The file system path for the *.spek file to load.
        :param validator: The validator to be used for validating the AST defining this module.
        """
        super().__init__(validator=validator)
        self._path = path

    def load_ast(self):
        with open(self._path, 'r') as file:
            lexer = SpektakelLexer(file)
            return SpektakelParser.parse_block(lexer)


class ASTModule(Module):
    """
    A module represented by an AST.
    """

    def __init__(self, node, env, dec, err):
        """
        Creates a new ASTModule.
        :param node: The abstract syntax tree (AST) defining this module.
        :param env: The environment mapping names defined in this module to their declarations.
        :param dec: The decorations for the AST definining this module.
        :param err: An iterable of all the validation errors in the AST defining this module.
        """
        super().__init__()
        self._ast = node
        self._dec = dec
        self._err = err
        self._env = env

    @property
    def ast(self):
        """
        The abstract syntax tree (AST) defining this module.
        """
        return self._ast

    @property
    def env(self):
        """
        The environment mapping names defined in this module to their declarations.
        :return: A dict mapping strings to AST nodes.
        """
        return self._env

    @property
    def dec(self):
        """
        The decorations for the AST definining this module.
        :return: A dict mapping AST nodes to their decorations.
        """
        return self._dec

    @property
    def err(self):
        """
        An iterable of all the validation errors in the AST defining this module.
        :return: An iterable of ValidationError objects.
        """
        return self._err

    @property
    def names(self):
        return self._env.keys()

    def resolve(self, name):
        return self._env[name]


class CompiledModule(Module):
    """
    A module mapping names to variables that are defined by pre-compiled definitions.
    """

    @property
    def names(self):
        raise NotImplementedError("CompiledModule has not been implemented yet!")

    def resolve(self, name):
        raise NotImplementedError("CompiledModule has not been implemented yet!")


class PythonModule(Module):
    """
    A module mapping names to variables that are defined by Python code.
    """
    @property
    def names(self):
        raise NotImplementedError("PythonModule has not been implemented yet!")

    def resolve(self, name):
        raise NotImplementedError("PythonModule has not been implemented yet!")
