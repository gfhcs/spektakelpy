import abc
import os.path
from io import StringIO

from engine.core.interaction import Interaction, i2s
from engine.stack.instructionset import Update, Pop
from engine.stack.procedure import StackProcedure
from engine.stack.program import StackProgram, ProgramLocation
from lang.modules import ModuleSpecification, Finder, AdjoinedFinder
from lang.spek.data import terms
from lang.spek.data.builtin import all_builtin
from lang.spek.data.references import ReturnValueReference
from lang.spek.data.terms import CRef, CTerm, CString, ITask, Read
from lang.spek.dynamic import Spektakel2Stack
from lang.spek.syntax import SpektakelLexer, SpektakelParser
from lang.validator import ValidationError


class BuiltinModuleSpecification(ModuleSpecification):
    """
    Specifies a module by explicitly mapping names to Values.
    """

    def __init__(self, name, symbols):
        """
        Maps names to Values in order to specify the contents of this module.
        :param name: The name of the builtin module.
        :param symbols: A mapping of names to Value objects.
        """
        super().__init__()
        self._name = name
        self._m = dict(symbols)

    @property
    def name(self):
        """
        The name of the builtin module specified by this object.
        """
        return self._name

    @property
    def symbols(self):
        """
        The mapping of names to Value objects that this module is defined by.
        """
        return dict(self._m)

    def resolve(self):

        code = []
        panic = 42
        r = CRef(ReturnValueReference())

        # Initialize a new namespace:
        code.append(Update(r, terms.NewDict([]), len(code) + 1, panic))

        # Map names to values:
        for name, value in self._m.items():
            code.append(Update(terms.Project(Read(r), CString(name)), CTerm(value), len(code) + 1, panic))

        # Return module:
        code.append(Pop(panic))

        return StackProgram(code)


class ASTModuleSpecification(ModuleSpecification, abc.ABC):
    """
    Specifies a module by an AST that is to be translated.
    """

    def __init__(self, validator, builtin):
        """
        Creates the specification for a module that is defined by an AST.
        :param validator: The validator to be used for validating the AST defining this module.
        :param builtin: An iterable of BuiltinModuleSpecification objects that define identifiers that are to be
                        builtin, i.e. valid without any explicit definition or import.
        """
        super().__init__()
        self._validator = validator
        self._builtin = builtin
        self._loading = False
        self._code = None

    @abc.abstractmethod
    def load_ast(self):
        """
        Loads the abstract syntax tree defining the contents of this module.
        """
        pass

    def resolve(self):
        if self._code is None:
            if self._loading:
                raise ValidationError("Circular reference: "
                                      "The loading of this module seems to depend on loading this module, "
                                      "i.e. there is a circular dependency somewhere!", None, None)
            try:
                self._loading = True
                ast = self.load_ast()
                env, dec, err = self._validator.validate(ast, mspec=self)
                if len(err) > 0:
                    raise err[0]
                translator = Spektakel2Stack(self._builtin)
                self._code = translator.translate_module([ast], dec).compile()
            finally:
                self._loading = False
        return self._code


class SpekStringModuleSpecification(ASTModuleSpecification):
    """
    Specifies a module that is to be loaded from a given string.
    """

    def __init__(self, code, validator, builtin):
        """
        Creates the specification for a module that is to be read from a source code string.
        :param code: The source code string to load parse and load as a module.
        :param validator: The validator to be used for validating the AST defining this module.
        :param builtin: An iterable of BuiltinModuleSpecification objects that define identifiers that are to be
                        builtin, i.e. valid without any explicit definition or import.
        """
        super().__init__(validator=validator, builtin=builtin)
        self._s = code

    def load_ast(self):
        return SpektakelParser.parse_block(SpektakelLexer(StringIO(self._s)))

    def __str__(self):
        return self._s


class SpekFileModuleSpecification(ASTModuleSpecification):
    """
    Specifies a module that is to be loaded from a *.spek file on disk.
    """

    def __init__(self, path, validator, builtin):
        """
        Creates the specification for a module that is to be loaded from a *.spek file.
        :param path: The file system path for the *.spek file to load.
        :param validator: The validator to be used for validating the AST defining this module.
        :param builtin: An iterable of BuiltinModuleSpecification objects that define identifiers that are to be
                        builtin, i.e. valid without any explicit definition or import.
        """
        super().__init__(validator=validator, builtin=builtin)
        self._path = path

    def load_ast(self):
        with open(self._path, 'r') as file:
            lexer = SpektakelLexer(file)
            return SpektakelParser.parse_block(lexer)

    def __str__(self):
        return self._path


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

    def find(self, name, validator, builtin):
        try:
            return self._cache[(validator, name)]
        except KeyError:

            for root in self._roots:
                path = os.path.join(root, *name[:-1], name[-1] + ".spek")
                if os.path.isfile(path):
                    spec = SpekFileModuleSpecification(path, validator=validator, builtin=builtin)
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
        :param mapping: A mapping of module names to dicts. Each dict is supposed to map module member
                        names to Value objects.
        """
        super().__init__()
        self._m = dict(mapping)

    def find(self, name, validator, builtin):
        if not isinstance(name, tuple) or len(name) != 1:
            raise KeyError("The module key {} could not be resolved!".format(".".join(name)))
        return self._m[name[0]]


def build_default_finder(roots):
    """
    Constructs the default Finder for Spektakelpy.
    :param roots: The root directories in the local file system that should be searched for imported modules.
    :return: A pair (f, b), where f is a Finder object and b is an iterable of BuiltinModuleSpecification objects whose
             names are to be imported by default.
    """
    ffinder = FileFinder(roots)

    symbols = {i2s(i).lower(): i for i in Interaction}

    procedures = {}
    r = CRef(ReturnValueReference())
    for name, symbol in symbols.items():
        p = StackProgram([Update(r, ITask(symbol), 1, 42), Pop(42)])
        procedures[name] = StackProcedure(0, ProgramLocation(p, 0))

    names = {name: value for name, value in all_builtin()}

    interaction = BuiltinModuleSpecification("interaction", procedures)
    builtin = BuiltinModuleSpecification("<builtin>", names)

    bfinder = BuiltinModuleFinder({mspec.name: mspec for mspec in [interaction, builtin]})

    return AdjoinedFinder(ffinder, bfinder), [builtin]
