from engine.core.data import VException
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


def unhashable(v):
    """
    Raises an exception informing about the given Value not being hashable.
    This abbreviation can be used to implement (by not implementing) Value.chash.
    :param v: The Value that is not hashable.
    """
    raise VTypeError("Unhashable type: '{v.type}'")
