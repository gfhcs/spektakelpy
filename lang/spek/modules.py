import abc
import os.path
from enum import Enum

from lang.modules import Module, ModuleSpecificaion, Finder, AdjoinedFinder
from lang.spek.syntax import SpektakelLexer, SpektakelParser
from lang.validator import ValidationError


class BuiltinModuleSpecification(ModuleSpecificaion):
    """
    Specifies that a module made up of builtin symbols is to be loaded.
    """

    def __init__(self, name, symbols):
        """
        Creates the specification for a module that is defined by an AST.
        :param name: The name of the builtin module.
        :param symbols: A dictionary mapping names to objects that represent the semantics of symbols.
        """
        super().__init__()
        self._name = name
        self._module = BuiltinModule(symbols)

    @property
    def name(self):
        """
        The name of the builtin module specified by this object.
        """
        return self._name

    def load(self):
        return self._module


class BuiltinModule(Module):
    """
    A module mapping names to variables that are defined by builtin semantics of the runtime environment.
    """

    def __init__(self, symbols):
        super().__init__()
        self._symbols = dict(symbols)

    @property
    def names(self):
        return self._symbols.keys()

    @property
    def errors(self):
        return []

    def resolve(self, name):
        return self._symbols[name]


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
                env, dec, err = self._validator.validate(ast, mspec=self)
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

    def __str__(self):
        return self._path


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
    def errors(self):
        return self._err

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
        return self._env.names

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


class BuiltinModuleFinder(Finder):
    """
    A finder that maps a list of names to BuiltinModuleSpecification objects.
    """

    def __init__(self, mapping):
        """
        Instantiates a new BuiltinModuleFinder.
        :param mapping: A dict-like object mapping names to BuildingModuleSpecification objects.
        """
        super().__init__()
        self._m = dict(mapping)

    def find(self, name, validator=None):
        if not isinstance(name, tuple) or len(name) != 1:
            raise KeyError("The module key {} could not be resolved!".format(".".join(name)))
        return self._m[name[0]]


class BuiltinAction(Enum):
    """
    Built-in action labels.
    """
    TICK = 0
    NEXT = 1
    PREV = 2


class BuiltinVariable(Enum):
    """
    Builtin variables.
    """
    TIME = 0


def build_default_finder(roots):
    ffinder = FileFinder(roots)
    m = [BuiltinModuleSpecification("interaction", {"next": BuiltinAction.NEXT,
                                                    "tick": BuiltinAction.TICK,
                                                    "prev": BuiltinAction.PREV}),
         BuiltinModuleSpecification("environment", {"time": BuiltinVariable.TIME})]
    bfinder = BuiltinModuleFinder({mspec.name: mspec for mspec in m})

    return AdjoinedFinder(ffinder, bfinder)
