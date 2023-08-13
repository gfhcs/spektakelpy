from engine.functional import Reference, Value
from engine.functional.values import VNamespace
from util import check_type
from util.immutable import check_sealed, check_unsealed


class FrameReference(Reference):
    """
    A reference to a value stored in the top-most stack frame of a task.
    """

    def __init__(self, index):
        """
        Refers to an entry in the topmost stack frame of a task.
        :param index: The index of the stack frame variable to refer to.
        """
        super().__init__()
        self._index = index

    def _seal(self):
        pass

    def clone_unsealed(self, clones=None):
        return FrameReference(self._index)

    def hash(self):
        check_sealed(self)
        return hash(self._index)

    def equals(self, other):
        return isinstance(other, FrameReference) and self._index == other._index

    def write(self, tstate, mstate, value):
        tstate.stack[-1][self._index] = value

    def read(self, tstate, mstate):
        return tstate.stack[-1][self._index]


class ReturnValueReference(Reference):
    """
    A reference to the value currently being returned from the callee to the caller.
    """

    def __init__(self):
        """
        Refers to a value that is to be returned.
        """
        super().__init__()

    def _seal(self):
        pass

    def clone_unsealed(self, clones=None):
        return ReturnValueReference()

    def hash(self):
        check_sealed(self)
        return 0

    def equals(self, other):
        return isinstance(other, ReturnValueReference)

    def write(self, tstate, mstate, value):
        tstate.returned = value

    def read(self, tstate, mstate):
        return tstate.returned


class ExceptionReference(Reference):
    """
    A reference to the exception currently being handled in a task.
    """

    def __init__(self):
        """
        Refers to the exception currently being handeled in a task.
        """
        super().__init__()

    def _seal(self):
        pass

    def clone_unsealed(self, clones=None):
        return ExceptionReference()

    def hash(self):
        check_sealed(self)
        return 0

    def equals(self, other):
        return isinstance(other, ExceptionReference)

    def write(self, tstate, mstate, value):
        check_unsealed(self)
        tstate.exception = value

    def read(self, tstate, mstate):
        return tstate.exception


class FieldReference(Reference):
    """
    A reference to the field of a runtime object.
    """

    def __init__(self, value, fidx):
        """
        Refers to a data field in a runtime object.
        :param value: The Value this reference is pointing into.
        :param fidx: The index of the field of the object that this reference is pointing to.
        """
        super().__init__()
        self._v = check_type(value, Value)
        self._fidx = check_type(fidx, int)

    def _seal(self):
        self._v.seal()

    def clone_unsealed(self, clones=None):
        return FieldReference(self._v.clone_unsealed(clones=clones))

    def hash(self):
        check_sealed(self)
        return hash((self._v, self._fidx))

    def equals(self, other):
        return isinstance(other, FieldReference) and self._fidx == other._fidx and self._v == other._v

    def write(self, tstate, mstate, value):
        self._v[self._fidx] = check_type(value, Value)

    def read(self, tstate, mstate):
        return self._v[self._fidx]


class NameReference(Reference):
    """
    A reference to a namespace entry.
    """

    def __init__(self, namespace, name):
        """
        Refers to a named field of an object.
        :param namespace: The namespace object this reference is referring to.
        :param name: The string name of the namespace entry to refer to.
        """
        super().__init__()
        self._ns = check_type(namespace, VNamespace)
        self._n = check_type(name, str)

    def _seal(self):
        self._ns.seal()

    def clone_unsealed(self, clones=None):
        return NameReference(self._ns.clone_unsealed(), self._n)

    def hash(self):
        check_sealed(self)
        return hash(self._ns) ^ hash(self._n)

    def equals(self, other):
        return isinstance(other, NameReference) and self._n == other._n and self._ns == other._ns

    def write(self, tstate, mstate, value):
        self._ns[self._n] = value

    def read(self, tstate, mstate):
        return self._ns[self._n]

