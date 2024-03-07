from engine.functional import Reference, Value
from engine.functional.values import VNamespace, VCell, VReferenceError, VTypeError
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
        return isinstance(other, VRef) and self._value.equals(other)

    def bequals(self, other, bijection):
        try:
            return bijection[id(self)] == id(other)
        except KeyError:
            bijection[id(self)] = id(other)
            return isinstance(other, VRef) and self._value.bequals(other, bijection)

    def cequals(self, other):
        return isinstance(other, VRef) and self._value.cequals(other)

    def write(self, tstate, mstate, value):
        raise VReferenceError("Cannot write to a VRef!")

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
        return self._index

    def equals(self, other):
        return isinstance(other, FrameReference) and self._index == other._index

    def bequals(self, other, bijection):
        return self.equals(other)

    def cequals(self, other):
        return self.equals(other)

    def write(self, tstate, mstate, value):
        # It is assumed that no exceptions are possible here, because calling Reference.write only happens during
        # execution of instructions, which in turn only happens when there still is a stack frame. Any exceptions
        # here thus point at implementation bugs of the virtual machine and should NOT be presented as "legitimate"
        # VException objects!
        frame = tstate.stack[-1]
        if len(frame) < self._index + 1:
            frame.resize(self._index + 1)
        frame[self._index] = value

    def read(self, tstate, mstate):
        try:
            return tstate.stack[-1][self._index]
        except IndexError as ex:
            raise VReferenceError(f"Could not read entry {self._index} from top stack frame!") from ex


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

    def bequals(self, other, bijection):
        return self.equals(other)

    def cequals(self, other):
        return self.equals(other)

    def write(self, tstate, mstate, value):
        try:
            frame = mstate.task_states[self._taskid].stack[self._offset]
        except IndexError as ex:
            raise VReferenceError(f"Failed to retrieve stack frame {self._offset} in task {self._taskid}!") from ex
        if len(frame) < self._index + 1:
            frame.resize(self._index + 1)
        frame[self._index] = value

    def read(self, tstate, mstate):
        try:
            return mstate.task_states[self._taskid].stack[self._offset][self._index]
        except IndexError as ex:
            raise VReferenceError(f"Failed to retrieve entry {self._index} of stack frame {self._offset} in task {self._taskid}!") from ex


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

    def bequals(self, other, bijection):
        return self.equals(other)

    def cequals(self, other):
        return self.equals(other)

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
        Refers to the exception currently being handled in a task.
        """
        super().__init__()
        self.seal()

    def print(self, out):
        return out.write("@exception")

    def _seal(self):
        pass

    def clone_unsealed(self, clones=None):
        return self

    def hash(self):
        return 1

    def equals(self, other):
        return isinstance(other, ExceptionReference)

    def bequals(self, other, bijection):
        return self.equals(other)

    def cequals(self, other):
        return self.equals(other)

    def write(self, tstate, mstate, value):
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
        return self._fidx

    def equals(self, other):
        return isinstance(other, FieldReference) and self._fidx == other._fidx and self._v.equals(other._v)

    def bequals(self, other, bijection):
        try:
            return bijection[id(self)] == id(other)
        except KeyError:
            bijection[id(self)] = id(other)
            return isinstance(other, FieldReference) and self._fidx == other._fidx and self._v.bequals(other._v, bijection)

    def cequals(self, other):
        return isinstance(other, FieldReference) and self._fidx == other._fidx and self._v.cequals(other._v)

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
        return hash(self._n)

    def equals(self, other):
        return isinstance(other, NameReference) and self._n == other._n and self._ns.equals(other._ns)

    def bequals(self, other, bijection):
        try:
            return bijection[id(self)] == id(other)
        except KeyError:
            bijection[id(self)] = id(other)
            return isinstance(other, NameReference) and self._n == other._n and self._ns.bequals(other._ns, bijection)

    def cequals(self, other):
        return isinstance(other, NameReference) and self._n == other._n and self._ns.cequals(other._ns)

    def write(self, tstate, mstate, value):
        ns = self._ns.read(tstate, mstate)
        if not isinstance(ns, VNamespace):
            raise VTypeError("NameReferences can only refer to VNamespace entries!")
        ns[self._n] = value

    def read(self, tstate, mstate):
        ns = self._ns.read(tstate, mstate)
        if not isinstance(ns, VNamespace):
            raise VTypeError("NameReferences can only refer to VNamespace entries!")
        return ns[self._n]


class CellReference(Reference):
    """
    Wraps a Reference that points to a VCell object. The CellReference reads/writes not the *cell*, but
    the *content* of the cell.
    """

    def __init__(self, cref):
        """
        Refers to cell.
        :param cref: A Reference to a memory location at which a cell object is stored.
        """
        super().__init__()
        self._cref = check_type(cref, Reference)

    @property
    def core(self):
        """
        The reference that points to the VCell object.
        :return: A Reference.
        """
        return self._cref

    def print(self, out):
        out.write("CellReference(")
        self._cref.print(out)
        out.write(")")

    def _seal(self):
        self._cref.seal()

    def clone_unsealed(self, clones=None):
        if clones is None:
            clones = {}
        try:
            return clones[id(self)]
        except KeyError:
            c = CellReference(self._cref)
            clones[id(self)] = c
            c._cref = c._cref.clone_unsealed(clones=clones)
            return c

    def hash(self):
        return hash(self._cref) ^ 987654

    def equals(self, other):
        return isinstance(other, CellReference) and self._cref.equals(other._cref)

    def bequals(self, other, bijection):
        return isinstance(other, CellReference) and self._cref.bequals(other._cref, bijection)

    def cequals(self, other):
        return isinstance(other, CellReference) and self._cref.cequals(other._cref)

    def write(self, tstate, mstate, value):
        cell = self._cref.read(tstate, mstate)
        if not isinstance(cell, VCell):
            raise VTypeError("CellReferences can only refer to VCell objects!")
        cell.value = value

    def read(self, tstate, mstate):
        cell = self._cref.read(tstate, mstate)
        if not isinstance(cell, VCell):
            raise VTypeError("CellReferences can only refer to VCell objects!")
        return cell.value
