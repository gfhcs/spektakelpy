from enum import Enum

from engine.core.atomic import type_object
from engine.core.exceptions import VCancellationError, VException
from engine.core.intrinsic import intrinsic_type, intrinsic_init, intrinsic_member
from engine.core.none import value_none
from engine.core.primitive import VBool
from engine.core.value import Value
from lang.spek.data.builtin import builtin
from lang.spek.data.exceptions import VFutureError
from util import check_type
from util.immutable import check_unsealed


class FutureStatus(Enum):
    UNSET = 0  # Future is in the state it was in at its initialization.
    SET = 1  # The result for the future has been set.
    FAILED = 2  # An exception for the future has been set.
    CANCELLED = 3  # The future has been cancelled.


@builtin()
@intrinsic_type("future", [type_object])
class VFuture(Value):
    """
    An object that represents a computation result that is not available yet.
    Its key feature is the fact that it can be awaited atomically in a guard expression.
    This makes sure that a Task can wait precisely until other tasks have made the kind of progress that it
    needs to make progress itself.
    """

    @intrinsic_init()
    def __init__(self):
        """
        Creates a new unset future.
        """
        super().__init__()
        self._status = FutureStatus.UNSET
        self._result = value_none

    def _print_status(self):
        return {FutureStatus.UNSET: "unset",
                FutureStatus.SET: "set",
                FutureStatus.FAILED: "failed",
                FutureStatus.CANCELLED: "cancelled"}[self._status]

    def print(self, out):
        out.write(f"future<{self._print_status()}>")

    def __repr__(self):
        return f"VFuture<{self._print_status()}>"

    @property
    def type(self):
        return VFuture.intrinsic_type

    def hash(self):
        return hash(self._status)

    def equals(self, other):
        return self is other

    def bequals(self, other, bijection):
        try:
            return bijection[id(self)] == id(other)
        except KeyError:
            bijection[id(self)] = id(other)
            return isinstance(other, VFuture) and self._status == other._status and self._result.bequals(other._result, bijection)

    def cequals(self, other):
        return self.equals(other)

    def _seal(self):
        if self._result is not None:
            self._result.seal()

    def clone_unsealed(self, clones=None):
        if clones is None:
            clones = {}
        try:
            return clones[id(self)]
        except KeyError:
            c = VFuture()
            clones[id(self)] = c
            c._status = self._status
            if self._result is not None:
                c._result = self._result.clone_unsealed(clones=clones)
            return c

    @property
    def status(self):
        """
        The status of this future.
        """
        return self._status

    @intrinsic_member()
    @property
    def done(self):
        """
        Indicates if a result for this future is either already available or cannot be expected anymore.
        """
        return VBool.from_bool(self._status != FutureStatus.UNSET)

    @intrinsic_member()
    def cancel(self):
        """
        Cancels this future, i.e. notifies all stakeholders that a completion of the computation it represents cannot
        be expected anymore. If the future is not UNSET anymore, calling this method does not change state.
        :return: True, if this method actually changed the state of the future, otherwise False.
        """
        check_unsealed(self)
        if self._status == FutureStatus.UNSET:
            self._status = FutureStatus.CANCELLED
            return VBool.true
        return VBool.false

    @intrinsic_member()
    @property
    def result(self):
        """
        The result that was set for this future.
        :return: The result that was set for this future.
        :exception: If this future is FAILED, the exception that was set for it will be *raised*.
        :except VFutureError: If this future is UNSET or CANCELLED.
        """
        if self._status == FutureStatus.UNSET:
            raise VFutureError("No result can be obtained for this future, because none has been set yet!")
        elif self._status == FutureStatus.SET:
            return self._result
        elif self._status == FutureStatus.CANCELLED:
            raise VCancellationError(initial=False, msg="Cannot retrieve the result for a future that has been cancelled!")
        elif self._status == FutureStatus.FAILED:
            raise self._result
        else:
            raise NotImplementedError(f"Handling {self._status} as not been implemented!")

    @result.setter
    def result(self, value):
        """
        Sets the result of this future and marks it as done.
        :param value: The result value to set.
        :exception VFutureError: If the future is already SET.
        :exception SealedException: If this future has been sealed.
        :exception TypeError: If the given value is not a proper Value.
        """
        check_unsealed(self)
        if self._status == FutureStatus.SET:
            raise VFutureError("This future has already been set!")
        self._result = check_type(value, Value)
        self._status = FutureStatus.SET

    @intrinsic_member()
    @property
    def exception(self):
        """
        The exception that was set on this future.
        :return: The VException that as set for this future. If a proper result was set, None is returned.
        :except VFutureError: If this future is UNSET or CANCELLED.
        """
        if self._status == FutureStatus.UNSET:
            raise VFutureError("Cannot retrieve the exception for a future that is still unset!")
        elif self._status == FutureStatus.SET:
            return None
        elif self._status == FutureStatus.CANCELLED:
            raise VFutureError("Cannot retrieve the exception for a future that has been cancelled!")
        elif self._status == FutureStatus.FAILED:
            return self._result
        else:
            raise NotImplementedError(f"Handling {self._status} as not been implemented!")

    @exception.setter
    def exception(self, value):
        """
        Sets an exception for this future.
        :param value: The VException value to set.
        :exception VFutureError: If the future is already SET.
        :exception SealedException: If this future has been sealed.
        :exception TypeError: If the given value is not a proper VException.
        """
        check_unsealed(self)
        if self._status == FutureStatus.SET:
            raise VFutureError("This future has already been set!")
        self._result = check_type(value, VException)
        self._status = FutureStatus.FAILED
