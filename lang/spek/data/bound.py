from engine.core.procedure import Procedure
from engine.core.value import Value
from engine.stack.exceptions import VTypeError
from util import check_type, check_types


class BoundProcedure(Procedure):
    """
    A procedure derived from another procedure by binding some of its parameters to given arguments.
    """

    def __init__(self, p, *args):
        """
        Binds some of the parameters of a procedure to fixed arguments.
        :param p: A Procedure.
        :param bound: A tuple of Value objects serving as arguments. Their number must be at most p.num_args, but
                      some of them may be None, to specify that the corresponding argument is not bound. If fewer than
                      p.num_args arguments are given, None will be appended until p.num_args is reached.
        """

        super().__init__()
        self._p = check_type(p, Procedure)

        if len(args) > p.num_args:
            raise ValueError(f"Expected at most {p.num_args} arguments, but got {len(args)}!")

        self._args = tuple(check_types(args, Value, allow_none=True)) + (None, ) * (p.num_args - len(args))
        self._num_args = p.num_args - sum(1 for x in self._args if x is not None)

    @property
    def num_args(self):
        return self._num_args

    def _seal(self):
        self._p.seal()
        for a in self._args:
            if a is not None:
                a.seal()

    def print(self, out):
        out.write(f"BoundProcedure(")
        prefix = ""
        for f in self._bound:
            out.write(prefix)
            f.print(out)
            prefix = ", "
        out.write(prefix)
        self._p.print(out)
        out.write(")")

    def hash(self):
        return len(self._args) ^ hash(self._p)

    def equals(self, other):
        return self is other

    def bequals(self, other, bijection):
        try:
            return bijection[id(self)] == id(other)
        except KeyError:
            bijection[id(self)] = id(other)
            if not (isinstance(other, BoundProcedure)
                    and self._num_args == other._num_args
                    and self._p.bequals(other._p, bijection)):
                return False

            for a, b in zip(self._args, other._args):
                if not (((a is None) == (b is None)) and (a is None or a.bequals(b, bijection))):
                    return False

            return True

    def cequals(self, other):
        return self.equals(other)

    def clone_unsealed(self, clones=None):
        if clones is None:
            clones = {}
        try:
            return clones[id(self)]
        except KeyError:
            c = BoundProcedure(self._p, *self._args)
            clones[id(self)] = c
            c._p = self._p.clone_unsealed(clones=clones)
            c._args = tuple(None if a is None else a.clone_unsealed(clones=clones) for a in self._args)
            return c

    def initiate(self, tstate, mstate, *args):
        if len(args) != self._num_args:
            raise VTypeError(f"Expected {self._num_args} arguments, but got {len(args)}!")

        local = list(self._args)
        args = iter(args)
        for idx, a in enumerate(self._args):
            if a is None:
                local[idx] = next(args)

        return self._p.initiate(tstate, mstate, *local)

