import abc
import os.path

from engine.functional import terms
from engine.functional.reference import ReturnValueReference
from engine.functional.terms import TRef, CTerm, CString, ITask
from engine.functional.types import TBuiltin
from engine.functional.values import VProcedure
from engine.tasks.instructions import Update, Pop, StackProgram, Guard
from engine.tasks.interaction import Interaction
from lang.modules import ModuleSpecification, Finder, AdjoinedFinder
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
        r = TRef(ReturnValueReference())

        # Initialize a new namespace:
        code.append(Update(r, terms.NewNamespace(), len(code) + 1, panic))

        # Map names to values:
        for name, value in self._m.items():
            code.append(Update(terms.Lookup(r, CString(name)), CTerm(value), len(code) + 1, panic))

        # Return module:
        code.append(Update(r, terms.NewModule(terms.Read(r)), len(code) + 1, panic))
        code.append(Pop())

        return StackProgram(code)


class ASTModuleSpecification(ModuleSpecification, abc.ABC):
    """
    Specifies a module by an AST that is to be translated.
    """

    def __init__(self, validator):
        """
        Creates the specification for a module that is defined by an AST.
        :param validator: The validator to be used for validating the AST defining this module.
        """
        super().__init__()
        self._validator = validator
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
                if len(err) > 1:
                    raise ValidationError("Validation failed because of one or more errors.", None, self)
                translator = Spektakel2Stack()
                self._code = translator.translate([ast], dec).compile()
            finally:
                self._loading = False
        return self._code


class SpekFileModuleSpecification(ASTModuleSpecification):
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
                    spec = SpekFileModuleSpecification(path, validator=validator)
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

    def find(self, name, validator=None):
        if not isinstance(name, tuple) or len(name) != 1:
            raise KeyError("The module key {} could not be resolved!".format(".".join(name)))
        return self._m[name[0]]


def build_default_finder(roots):
    ffinder = FileFinder(roots)

    symbols = {"next": Interaction.NEXT,
               "tick": Interaction.TICK,
               "prev": Interaction.PREV,
               "never": Interaction.NEVER}

    procedures = {}
    r = TRef(ReturnValueReference())
    for name, symbol in symbols:
        procedures[name] = VProcedure(0, StackProgram([Update(r, ITask(symbol), 1, 42), Pop()]))

    types = {t.name: t for t in TBuiltin.instances}

    m = [BuiltinModuleSpecification("interaction", procedures),
         BuiltinModuleSpecification("<builtin>", types)]
    bfinder = BuiltinModuleFinder({mspec.name: mspec for mspec in m})

    return AdjoinedFinder(ffinder, bfinder)
