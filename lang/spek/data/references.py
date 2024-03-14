from engine.core.finite import FiniteValue
from engine.core.keyable import KeyableValue
from engine.core.singleton import SingletonValue
from engine.core.value import Value
from engine.stack.exceptions import VReferenceError, VTypeError
from engine.stack.reference import Reference
from lang.spek.data.cells import VCell
from lang.spek.data.values import VNamespace
from util import check_type
from util.immutable import Immutable


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
            c = VRef(self._value)
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


class FrameReference(FiniteValue, Reference):
    """
    A reference to a value stored in the top-most stack frame of a task.
    """

    def __init__(self, index):
        """
        Refers to an entry in the topmost stack frame of a task.
        :param index: The index of the stack frame variable to refer to.
        """
        # __new__ is taking care of the index.
        super().__init__()

    @property
    def index(self):
        """
        The index of the stack frame variable to refer to.
        :return:
        """
        return self.instance_index

    def print(self, out):
        out.write(f"@{self.index}")

    def write(self, tstate, mstate, value):
        # It is assumed that no exceptions are possible here, because calling Reference.write only happens during
        # execution of instructions, which in turn only happens when there still is a stack frame. Any exceptions
        # here thus point at implementation bugs of the virtual machine and should NOT be presented as "legitimate"
        # VException objects!
        frame = tstate.stack[-1]
        if len(frame) < self.index + 1:
            frame.resize(self.index + 1)
        frame[self.index] = value

    def read(self, tstate, mstate):
        try:
            return tstate.stack[-1][self.index]
        except IndexError as ex:
            raise VReferenceError(f"Could not read entry {self.index} from top stack frame!") from ex


class AbsoluteFrameReference(KeyableValue, Reference):
    """
    A reference to a value stored in a stack frame that is addressed explicitly.
    This reference will always evaluate to the same value regardless of the task that interprets it.
    """

    def __new__(cls, taskid, offset, index, *args, **kwargs):
        return super().__new__(cls, (taskid, offset, index), *args, **kwargs)

    def __init__(self, taskid, offset, index):
        """
        Refers to a stack frame entry in a way that leads to the same value no matter which Task interprets the
        reference.
        :param taskid: The ID of the task the referenced stack frame belongs to.
        :param offset: The offset (from the base) in the task stack at which the reference stack frame is found.
        :param index: The index of the stack frame variable to refer to.
        """
        # KeyableValue.__new__ already took care of the arguments.
        super().__init__()

    def print(self, out):
        t, o, i = self.instance_key
        return out.write(f"@({t}, {o}, {i})")

    def write(self, tstate, mstate, value):
        t, o, i = self.instance_key
        try:
            frame = mstate.task_states[t].stack[o]
        except IndexError as ex:
            raise VReferenceError(f"Failed to retrieve stack frame {o} in task {t}!") from ex
        if len(frame) < i + 1:
            frame.resize(i + 1)
        frame[i] = value

    def read(self, tstate, mstate):
        t, o, i = self.instance_key
        try:
            return mstate.task_states[t].stack[o][i]
        except IndexError as ex:
            raise VReferenceError(f"Failed to retrieve entry {i} of stack frame {o} in task {t}!") from ex


class ReturnValueReference(SingletonValue, Reference):
    """
    A reference to the value currently being returned from the callee to the caller.
    """

    def print(self, out):
        return out.write("@return")

    def write(self, tstate, mstate, value):
        tstate.returned = value

    def read(self, tstate, mstate):
        return tstate.returned


class ExceptionReference(SingletonValue, Reference):
    """
    A reference to the exception currently being handled in a task.
    """

    def print(self, out):
        return out.write("@exception")

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


class ItemReference(Reference):
    """
    A reference to an indexed item of a data structure.
    """

    def __init__(self, structure, index):
        """
        Refers to an indexed item of a data structure.
        :param structure: A Value representing the indexed data structure.
        :param index: A Value representing the index.
        """
        super().__init__()
        self._structure = check_type(structure, Value)
        self._index = check_type(index, Value)

    def _seal(self):
        self._structure.seal()
        self._index.seal()

    def hash(self):
        return hash(self._index)

    def equals(self, other):
        return isinstance(other, ItemReference) and (self._structure, self._index) == (other._structure, other._index)

    def bequals(self, other, bijection):
        try:
            return bijection[id(self)] == id(other)
        except KeyError:
            bijection[id(self)] = id(other)
            return (isinstance(other, ItemReference)
                    and self._structure.bequals(other._structure, bijection)
                    and self._index.bequals(other._index, bijection))

    def cequals(self, other):
        return (isinstance(other, ItemReference)
                and self._structure.cequals(other._structure)
                and self._index.cequals(other._index))

    def clone_unsealed(self, clones=None):
        if clones is None:
            clones = {}
        try:
            return clones[id(self)]
        except KeyError:
            c = ItemReference(self._structure, self._index)
            clones[id(self)] = c
            c._structure = self._structure.clone_unsealed(clones=clones)
            c._index = self._index.clone_unsealed(clones=clones)
            return c

    def print(self, out):
        self._structure.print(out)
        out.write("[")
        self._index.print(out)
        out.write("]")

    def read(self, tstate, mstate):
        try:
            return self._structure[self._index]
        except AttributeError:
            raise VTypeError(f"Values of type {self._structure.type} cannot be projected!")

    def write(self, tstate, mstate, value):
        try:
            self._structure[self._index] = value
        except AttributeError:
            raise VTypeError(f"Values of type {self._structure.type} do not allow writing to projection items!")


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
