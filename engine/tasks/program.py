from engine.functional import Value
from engine.functional.types import TBuiltin, builtin_type
from engine.tasks import Instruction
from util import check_type
from util.immutable import Immutable, check_sealed
from util.printable import Printable


class StackProgram(Printable, Immutable):
    """
    An array of stack machine instructions. Each instruction updates the state of a stack machine, in particular
    determining which instruction to execute next.
    """

    def __init__(self, instructions):
        """
        Creates a new stack program.
        :param instructions: An iterable of Instruction objects.
        """
        super().__init__()
        self._instructions = tuple(check_type(i, Instruction) for i in instructions)

    def print(self, out):
        out.write("StackProgram ")
        out.write(str(id(self)))
        out.write(":")
        for idx, i in enumerate(self._instructions):
            out.write(f"\n{idx}: ")
            i.print(out)

    def hash(self):
        return len(self._instructions)

    def equals(self, other):
        return isinstance(other, StackProgram) and self._instructions == other._instructions

    def __len__(self):
        return self._instructions

    def __iter__(self):
        return iter(self._instructions)

    def __getitem__(self, item):
        return self._instructions[item]


@builtin_type("location", [TBuiltin.object])
class ProgramLocation(Immutable, Value):
    """
    A pair of StackProgram and instruction index.
    """

    @property
    def type(self):
        return TBuiltin.location

    def __init__(self, program, index):
        """
        Creates a new program location.
        :param program: The StackProgram this object is pointing into.
        :param index: The index of the instruction in the given stack program that this location is pointing to.
        """

        super().__init__()
        self._program = check_type(program, StackProgram)
        self._index = check_type(index, int)

        if not program.sealed:
            raise ValueError("The given program must be sealed!")

    def print(self, out):
        out.write(f"<Line {self._index} of StackProgram {id(self._program)}>")

    @property
    def program(self):
        """
        The StackProgram this object is pointing into.
        """
        return self._program

    @property
    def index(self):
        """
        The index of the instruction in the given stack program that this location is pointing to.
        """
        return self._index

    def hash(self):
        check_sealed(self)
        return self._index

    def equals(self, other):
        return isinstance(other, ProgramLocation) and (self._index, self._program) == (other._index, other._program)

    def bequals(self, other, bijection):
        return self.equals(other)

    def cequals(self, other):
        return self.equals(other)
