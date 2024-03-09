from engine.core.exceptions import VException
from engine.core.intrinsic import intrinsic


@intrinsic("ReferenceError")
class VReferenceError(VException):
    """
    Raised when accessing a Reference has failed.
    """
    pass


@intrinsic("TypeError")
class VTypeError(VException):
    """
    Raised when an inappropriate type is encountered.
    """
    pass


@intrinsic("InstructionException")
class VInstructionException(VException):
    """
    Raised when the execution of an instruction fails.
    """
    pass
