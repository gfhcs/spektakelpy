from engine.core.procedure import Procedure
from engine.stack.exceptions import VTypeError
from engine.stack.frame import Frame
from engine.stack.program import ProgramLocation
from util import check_type
from util.immutable import Immutable


class StackProcedure(Immutable, Procedure):
    """
    A procedure that is implemented by virtual machine instructions.
    """

    def __init__(self, num_args, entry):
        """
        Creates a new stack procedure.
        :param num_args: The number of arguments of this procedure.
        :param entry: A ProgramLocation that points to the entry point for this procedure.
        """
        super().__init__()
        self._num_args = check_type(num_args, int)
        self._entry = check_type(entry, ProgramLocation)

    @property
    def num_args(self):
        return self._num_args

    @property
    def entry(self):
        """
        A ProgramLocation that points to the entry point for this procedure.
        """
        return self._entry

    def print(self, out):
        out.write(f"StackProcedure({self._num_args}, ")
        self._entry.print(out)
        out.write(")")

    def hash(self):
        return self._num_args ^ len(self._entry.program)

    def equals(self, other):
        return self is other

    def bequals(self, other, bijection):
        try:
            return bijection[id(self)] == id(other)
        except KeyError:
            bijection[id(self)] = id(other)
            return (isinstance(other, StackProcedure)
                    and self._num_args == other._num_args
                    and self._entry.bequals(other._entry, bijection))

    def cequals(self, other):
        return self.equals(other)

    def initiate(self, tstate, mstate, *args):
        if len(args) != self._num_args:
            raise VTypeError(f"Expected {self._num_args} arguments, but got {len(args)}!")
        tstate.push(Frame(self._entry, args))
        return None
