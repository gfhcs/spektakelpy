import abc

from engine.functional.values import Value
from util import check_type
from util.immutable import check_sealed, check_unsealed


class Reference(Value, abc.ABC):
    """
    A reference is a part of a machine state that can point to another part of a machine state.
    """

    def type(self):
        from engine.functional.types import TBuiltin
        return TBuiltin.ref

    @abc.abstractmethod
    def write(self, tstate, mstate, value):
        """
        Updates the value stored at the location that this reference is pointing to.
        :param tstate: The TaskState in the context of which this reference is to be interpreted. It must be part
                       of the given mstate.
        :param mstate: The MachineState in the context of which this reference is to be interpreted. It must contain
                       tstate.
        :param value: The value to store at the location that this reference is pointing to.
        """
        pass

    @abc.abstractmethod
    def read(self, tstate, mstate):
        """
        Obtains the value that this reference is pointing to.
        :param tstate: The TaskState in the context of which this reference is to be interpreted. It must be part
                       of the given mstate.
        :param mstate: The MachineState in the context of which this reference is to be interpreted. It must contain
                       tstate.
        :return: The object pointed to by this reference.
        """
        pass


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
    A reference to a named field of an object.
    """

    def __init__(self, oref, name):
        """
        Refers to a named field of an object.
        :param oref: A Reference to the object a field of which is to be referenced.
        :param name: The name of the field to refer to.
        """
        super().__init__()
        self._oref = oref
        self._name = name

    def _seal(self):
        self._oref.seal()

    def clone_unsealed(self, clones=None):
        return NameReference(self._oref.clone_unsealed(), self._name)

    def hash(self):
        check_sealed(self)
        return hash(self._oref) ^ hash(self._name)

    def equals(self, other):
        return isinstance(other, NameReference) and self._name == other._name and self._oref == other._oref

    def write(self, tstate, mstate, value):
        self._oref.read(tstate, mstate)[self._name] = value

    def read(self, tstate, mstate):
        return self._oref.read(tstate, mstate)[self._name]

