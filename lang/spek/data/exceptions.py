from engine.core.exceptions import VException
from engine.core.intrinsic import intrinsic
from lang.spek.data.builtin import builtin


@intrinsic("JumpError")
class VJumpError(VException):
    """
    Raised a control flow jump is executed.
    """

    def __init__(self, msg):
        super().__init__(msg)

    def hash(self):
        return hash(self._msg)

    def clone_unsealed(self, clones=None):
        if clones is None:
            clones = {}
        try:
            return clones[id(self)]
        except KeyError:
            c = type(self)()
            clones[id(self)] = c
            return c


@intrinsic("ReturnError")
class VReturnError(VJumpError):
    """
    Raised a return statement is executed.
    """
    def __init__(self):
        super().__init__("A procedure return is being executed!")


@intrinsic("BreakError")
class VBreakError(VJumpError):
    """
    Raised a break statement is executed.
    """
    def __init__(self):
        super().__init__("An escape from a loop is being executed!")


@intrinsic("ContinueError")
class VContinueError(VJumpError):
    """
    Raised a continue statement is executed.
    """
    def __init__(self):
        super().__init__("A remainder of a loop body is being skipped!")


@builtin()
@intrinsic("AttributeError")
class VAttributeError(VException):
    """
    Raised when an attribute cannot be resolved.
    """
    pass


@builtin()
@intrinsic("IndexError")
class VIndexError(VException):
    """
    Spek equivalent of Python's IndexError.
    """
    pass


@builtin()
@intrinsic("FutureError")
class VFutureError(VException):
    """
    Raised when the state of a Future does not allow an operation.
    """
    pass
