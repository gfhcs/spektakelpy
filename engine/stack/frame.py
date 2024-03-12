from engine.core.none import VNone
from engine.core.value import Value
from engine.stack.program import ProgramLocation
from util import check_type, check_types
from util.immutable import check_sealed, check_unsealed


class Frame(Value):
    """
    Represents a set of local variables and a pointer to the next machine instruction to execute.
    """

    def __init__(self, location, local_values):
        """
        Allocates a new stack frame.
        :param location: The program location of the instruction that is to be executed next.
        :param local_values: The array of values of the local variables stored in this stack frame.
        """
        super().__init__()
        self._location = check_type(location, ProgramLocation)
        self._local_values = list(check_types(local_values, Value))

    @property
    def type(self):
        raise NotImplementedError("Stack frames and their types are supposed to not be visible for machine programs!")

    def __len__(self):
        return len(self._local_values)

    def resize(self, new_length):
        """
        Changes the number of local variables in this stack frame.
        :param new_length: The new number of local variables in this stack frame.
        """
        d = new_length - len(self._local_values)
        if d > 0:
            self._local_values.extend([VNone.instance] * d)
        elif d < 0:
            self._local_values = self._local_values[:d]

    def print(self, out):
        out.write("Frame@")
        self._location.print(out)
        out.write(": [")
        prefix = ""
        for v in self._local_values:
            out.write(prefix)
            v.print(out)
            prefix = ", "
        out.write("]")

    def _seal(self):
        self._location.seal()
        for v in self._local_values:
            v.seal()
        self._local_values = tuple(self._local_values)

    def clone_unsealed(self, clones=None):
        if clones is None:
            clones = {}
        try:
            return clones[id(self)]
        except KeyError:
            c = Frame(self._location, self._local_values)
            clones[id(self)] = c
            c._location = c._location.clone_unsealed(clones)
            c._local_values = [v.clone_unsealed(clones=clones) for v in c._local_values]
            return c

    def hash(self):
        check_sealed(self)
        return len(self._local_values)

    def equals(self, other):
        return (isinstance(other, Frame)
                and len(self._local_values) == len(other._local_values)
                and self._location.equals(other._location)
                and all(a.equals(b) for a, b in zip(self._local_values, other._local_values)))

    def bequals(self, other, bijection):
        try:
            return bijection[id(self)] == id(other)
        except KeyError:
            bijection[id(self)] = id(other)
            if not (isinstance(other, Frame)
                    and len(self._local_values) == len(other._local_values)
                    and self._location.bequals(other._location, bijection)):
                return False
            return all(a.bequals(b, bijection) for a, b in zip(self._local_values, other._local_values))

    def cequals(self, other):
        return self.equals(other)

    @property
    def program(self):
        """
        The machine program to which this stack frame belongs.
        """
        return self._location.program

    @property
    def instruction_index(self):
        """
        The index of the instruction in the given program that is to be executed next.
        """
        return self._location.index

    @instruction_index.setter
    def instruction_index(self, value):
        check_unsealed(self)
        self._location = ProgramLocation(self._location.program, value)

    @property
    def local(self):
        """
        The array of values of the local variables stored in this stack frame.
        """
        return tuple(self._local_values)

    def set_local(self, index, value):
        """
        Updates a local variable recorded in this frame.
        :param index: The index of the local variable to update.
        :param value: The new value for the local variable.
        """
        check_unsealed(self)
        self._local_values[index] = check_type(value, Value)

    def __getitem__(self, index):
        return self.local[index]

    def __setitem__(self, index, value):
        self.set_local(index, value)
