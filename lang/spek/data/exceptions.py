from enum import Enum, IntEnum

from engine.core.exceptions import VException
from engine.core.intrinsic import intrinsic_type
from lang.spek.data.builtin import builtin
from util import check_type
from util.finite import Finite


class JumpType(IntEnum):
    """
    Describes the reason for an unconditional jump in a machine program resulting from a Spek program.
    """
    RETURN = 0
    BREAK = 1
    CONTINUE = 2


@intrinsic_type("JumpError")
class VJumpError(Finite, VException):
    """
    Raised a control flow jump is executed.
    """
    def __init__(self, reason):
        """
        Creates a new jump error.
        :param reason: The JumpType justifying this error.
        """
        super().__init__(f"An unconditional jump is being executed. Reason: {reason}")
        self._reason = check_type(reason, JumpType)

    @property
    def reason(self):
        """
        The JumpType justifying this error.
        """
        return self._reason


@builtin()
@intrinsic_type("AttributeError")
class VAttributeError(VException):
    """
    Raised when an attribute cannot be resolved.
    """
    pass


@builtin()
@intrinsic_type("IndexError")
class VIndexError(VException):
    """
    Spek equivalent of Python's IndexError.
    """
    pass


@builtin()
@intrinsic_type("KeyError")
class VKeyError(VException):
    """
    Raised when a mapping is missing a requested key.
    """
    pass


@builtin()
@intrinsic_type("FutureError")
class VFutureError(VException):
    """
    Raised when the state of a Future does not allow an operation.
    """
    pass
