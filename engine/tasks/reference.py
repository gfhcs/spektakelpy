import abc

from engine.functional.values import Value
from util import check_type
from util.immutable import Sealable, check_sealed, check_unsealed


class Reference(Sealable, abc.ABC):
    """
    A reference is a part of a machine state that can point to another part of a machine state.
    """

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
        check_unsealed(self)
        tstate.stack[-1].local[self._index] = value

    def read(self, tstate, mstate):
        return tstate.stack[-1].local[self._index]


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
        check_unsealed(self)
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


class ObjectReference(Reference):
    """
    A reference to a heap object. Instead of holding offsets into an explicit heap, references of this
    kind directly point at Python objects. This makes sure that no explicit garbage collection needs to be implemented
    """

    def __init__(self, pobject):
        """
        Refers to a value in the machine's heap memory.
        :param pobject: The Python object this reference is pointing to. It must be a Value.
        """
        super().__init__()
        self._pobject = check_type(pobject, Value)

    def _seal(self):
        self._pobject.seal()

    def clone_unsealed(self, clones=None):
        return ObjectReference(self._pobject.clone_unsealed(clones=clones))

    def hash(self):
        check_sealed(self)
        return hash(self._pobject)

    def equals(self, other):
        return isinstance(other, ObjectReference) and self._pobject == other._pobject

    def write(self, tstate, mstate, value):
        raise Exception("Overriding an object via an ObjectReference is not possible!")

    def read(self, tstate, mstate):
        return self._pobject


