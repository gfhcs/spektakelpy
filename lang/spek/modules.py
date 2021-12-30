import abc

from lang.modules import Module, ModuleSpecificaion, Finder
from lang.validator import ValidationError
from lang.spek.syntax import SpektakelLexer, SpektakelParser
import os.path


class ASTSpecification(ModuleSpecificaion, abc.ABC):
    """
    Specifies that an ASTModule is to be loaded.
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
                raise ValidationError("Circular reference: "
                                      "The loading of this module seems to depend on loading this module, "
                                      "i.e. there is a circular dependency somewhere!", None, None)
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


class FileFinder(Finder):
    """
    A finder that maps module names to file system paths to *.spek files.
    """

    def __init__(self, roots):
        """
        Instantiates a new FileFinder.
        :param roots: An iterable of file system directory paths. They will be searched for modules in the given order.
        """
        super().__init__()
        self._roots = list(roots)
        self._cache = {}

    @property
    def roots(self):
        """
        The file system directories that are searched for *.spek files.
        :return: A list of strings.
        """
        return self._roots

    def find(self, name, validator=None):
        try:
            return self._cache[(validator, name)]
        except KeyError:

            for root in self._roots:
                path = os.path.join(root, *name[:-1], name[-1] + ".spek")
                if os.path.isfile(path):
                    spec = SpekFileSpecification(path, validator=validator)
                    self._cache[(validator, name)] = spec
                    return spec

            raise KeyError("No *.spek file could be found for the name {}!".format(name))

