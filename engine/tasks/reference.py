import abc
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

    def clone_unsealed(self):
        return FrameReference(self._index)

    def hash(self):
        check_sealed(self)
        return hash(self._index)

    def equals(self, other):
        return isinstance(other, FrameReference) and self._index == other._index

    def write(self, tstate, mstate, value):
        check_unsealed(self)
        tstate.stack[0].local[self._index] = value

    def read(self, tstate, mstate):
        return tstate.stack[0].local[self._index]


class HeapReference(Reference):
    """
    A reference to a value stored in the heap memory of the machine.
    """

    def __init__(self, index):
        """
        Refers to a value in the machine's heap memory.
        :param index: An index into the heap memory.
        """
        super().__init__()
        self._index = index

    def _seal(self):
        pass

    def clone_unsealed(self):
        return HeapReference(self._index)

    def hash(self):
        check_sealed(self)
        return hash(self._index)

    def equals(self, other):
        return isinstance(other, HeapReference) and self._index == other._index

    def write(self, tstate, mstate, value):
        check_unsealed(self)
        mstate.heap[self._index] = value

    def read(self, tstate, mstate):
        return mstate.heap[self._index]


class ReturnValueReference(Reference):
    """
    A reference to the value currently being returned from the callee to the caller.
    """

    def __init__(self):
        """
        Refers to a value in the machine's heap memory.
        :param index: An index into the heap memory.
        """
        super().__init__()

    def _seal(self):
        pass

    def clone_unsealed(self):
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
        Refers to a value in the machine's heap memory.
        :param index: An index into the heap memory.
        """
        super().__init__()

    def _seal(self):
        pass

    def clone_unsealed(self):
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
