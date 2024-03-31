from engine.core.procedure import Procedure
from engine.core.value import Value
from util import check_type, check_types


class BoundProcedure(Procedure):
    """
    A procedure derived from another procedure by binding some of its parameters to given arguments.
    """

    def __init__(self, p, *args):
        """
        Binds some of the parameters of a procedure to fixed arguments.
        :param p: A Procedure.
        :param bound: A tuple of Value objects serving as arguments. Some of them may be None,
                      to specify that the corresponding argument is not bound.
        """

        super().__init__()
        self._p = check_type(p, Procedure)
        self._args = check_types(args, Value, allow_none=True)

    def _seal(self):
        self._p.seal()
        for a in self._args:
            if a is not None:
                a.seal()

    def print(self, out):
        out.write(f"BoundProcedure(")
        prefix = ""
        for f in self._args:
            out.write(prefix)
            f.print(out)
            prefix = ", "
        out.write(prefix)
        self._p.print(out)
        out.write(")")

    def hash(self):
        return len(self._args) ^ hash(self._p)

    def equals(self, other):
        return (isinstance(other, BoundProcedure)
                and self._p.equals(other._p)
                and all(((a is None) == (b is None)) and (a is None or a.equals(b)) for a, b in zip(self._args, other._args)))

    def bequals(self, other, bijection):
        try:
            return bijection[id(self)] == id(other)
        except KeyError:
            bijection[id(self)] = id(other)
            if not (isinstance(other, BoundProcedure)
                    and self._p.bequals(other._p, bijection)):
                return False

            for a, b in zip(self._args, other._args):
                if not (((a is None) == (b is None)) and (a is None or a.bequals(b, bijection))):
                    return False

            return True

    def cequals(self, other):
        return (isinstance(other, BoundProcedure)
                and self._p.cequals(other._p)
                and all(((a is None) == (b is None)) and (a is None or a.cequals(b)) for a, b in zip(self._args, other._args)))

    def chash(self):
        return self._p.chash() ^ hash((a.chash() for a in self._args))

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
        expected = sum(1 for a in self._args if a is None)
        received = len(args)
        if received < expected:
            raise ValueError(f"Expected at least {expected} arguments, but got only {received}!")

        local = list(self._args)
        args = iter(args)
        for idx, a in enumerate(self._args):
            if a is None:
                local[idx] = next(args)

        for a in args:
            local.append(a)

        return self._p.initiate(tstate, mstate, *local)

