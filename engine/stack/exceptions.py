from engine.core.exceptions import VException
from engine.core.intrinsic import intrinsic_type


@intrinsic_type("ReferenceError")
class VReferenceError(VException):
    """
    Raised when accessing a Reference has failed.
    """
    pass


@intrinsic_type("TypeError")
class VTypeError(VException):
    """
    Raised when an inappropriate type is encountered.
    """
    pass


@intrinsic_type("InstructionException")
class VInstructionException(VException):
    """
    Raised when the execution of an instruction fails.
    """
    pass
