from engine.functional import Reference, Value
from engine.functional.values import VNamespace
from util import check_type
from util.immutable import check_unsealed


class VRef(Reference):
    """
    A reference that represents a Value.
    """

    def __init__(self, value):
        """
        Refers to a runtime value.
        :param value: The value this reference is to refer to.
        """
        super().__init__()
        self._value = check_type(value, Value)

    def print(self, out):
        self._value.print(out)

    def _seal(self):
        self._value.seal()

    def clone_unsealed(self, clones=None):
        if clones is None:
            clones = {}
        try:
            return clones[id(self)]
        except KeyError:
            c = VRef()
            clones[id(self)] = c
            c._value = self._value.clone_unsealed(clones=clones)
            return c

    def hash(self):
        return hash(self._value)

    def equals(self, other):
        return isinstance(other, VRef) and self._value == other._value

    def write(self, tstate, mstate, value):
        raise RuntimeError("Cannot write to a VRef!")

    def read(self, tstate, mstate):
        return self._value


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

    @property
    def index(self):
        """
        The index of the stack frame variable to refer to.
        :return:
        """
        return self._index

    def print(self, out):
        out.write(f"@{self._index}")

    def _seal(self):
        pass

    def clone_unsealed(self, clones=None):
        return self

    def hash(self):
        return hash(self._index)

    def equals(self, other):
        return isinstance(other, FrameReference) and self._index == other._index

    def write(self, tstate, mstate, value):
        tstate.stack[-1][self._index] = value

    def read(self, tstate, mstate):
        return tstate.stack[-1][self._index]


class AbsoluteFrameReference(Reference):
    """
    A reference to a value stored in a stack frame that is addressed explicitly.
    This reference will always evaluate to the same value regardless of the task that interprets it.
    """

    def __init__(self, taskid, offset, index):
        """
        Refers to a stack frame entry in a way that leads to the same value no matter which Task interprets the
        reference.
        :param taskid: The ID of the task the referenced stack frame belongs to.
        :param offset: The offset (from the base) in the task stack at which the reference stack frame is found.
        :param index: The index of the stack frame variable to refer to.
        """
        super().__init__()
        self._taskid = taskid
        self._offset = offset
        self._index = index

    def print(self, out):
        return out.write(f"@({self._taskid}, {self._offset}, {self._index})")

    def _seal(self):
        pass

    def clone_unsealed(self, clones=None):
        return self

    def hash(self):
        return hash((self._taskid, self._offset, self._index))

    def equals(self, other):
        return isinstance(other, AbsoluteFrameReference) and (self._taskid, self._offset, self._index) == (other._taskid, other._offset, other._index)

    def write(self, tstate, mstate, value):
        mstate.task_states[self._taskid].stack[self._offset][self._index] = value

    def read(self, tstate, mstate):
        return mstate.task_states[self._taskid].stack[self._offset][self._index]


class ReturnValueReference(Reference):
    """
    A reference to the value currently being returned from the callee to the caller.
    """

    def __init__(self):
        """
        Refers to a value that is to be returned.
        """
        super().__init__()

    def print(self, out):
        return out.write("@return")

    def _seal(self):
        pass

    def clone_unsealed(self, clones=None):
        return self

    def hash(self):
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

    def print(self, out):
        return out.write("@exception")

    def _seal(self):
        pass

    def clone_unsealed(self, clones=None):
        return self

    def hash(self):
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

    def print(self, out):
        self._v.print(out)
        out.write(f".{self._fidx}")

    def _seal(self):
        self._v.seal()

    def clone_unsealed(self, clones=None):
        if clones is None:
            clones = {}
        try:
            return clones[id(self)]
        except KeyError:
            c = FieldReference(self._v, self._fidx)
            clones[id(self)] = c
            c._v = c._v.clone_unsealed(clones=clones)
            return c

    def hash(self):
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
        :param namespace: A Reference pointing to a Namespace object.
        :param name: The string name of the namespace entry to refer to.
        """
        super().__init__()
        self._ns = check_type(namespace, Reference)
        self._n = check_type(name, str)

    def print(self, out):
        self._ns.print(out)
        out.write(f".{self._n}")

    def _seal(self):
        self._ns.seal()

    def clone_unsealed(self, clones=None):
        if clones is None:
            clones = {}
        try:
            return clones[id(self)]
        except KeyError:
            c = NameReference(self._ns, self._n)
            clones[id(self)] = c
            c._ns = c._ns.clone_unsealed(clones=clones)
            return c

    def hash(self):
        return hash(self._ns) ^ hash(self._n)

    def equals(self, other):
        return isinstance(other, NameReference) and self._n == other._n and self._ns == other._ns

    def write(self, tstate, mstate, value):
        ns = self._ns.read(tstate, mstate)
        if not isinstance(ns, VNamespace):
            raise TypeError("NameReferences can only refer to VNamespace entries!")
        ns[self._n] = value

    def read(self, tstate, mstate):
        ns = self._ns.read(tstate, mstate)
        if not isinstance(ns, VNamespace):
            raise TypeError("NameReferences can only refer to VNamespace entries!")
        return ns[self._n]

