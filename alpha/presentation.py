from core.process import *
from enum import Enum
from alpha.behavior import *


class Action(Interaction):
    """
    A way of interacting with a presentation.
    """

    class Label(Enum):
        """
        Specifies the type of interaction that an Action object represents.
        """
        FORWARD = 1
        ESCAPE = 0
        BACKWARD = 2

    def __init__(self, label, *largs):
        """
        Instantiates a new action to be applied on a presentation.
        :param label: The label of this action.
        :param largs: The arguments for this action. The number and types of these arguments are determined by the label.
        """
        super().__init__()
        self._label = label
        self._args = largs

        if len(largs) != 0:
            raise ValueError("The action label '{}' does not take any parameters!".format(label))

    def equal(self, other):
        if not isinstance(other, Action):
            return False
        return self._label == other._label and self._args == other._args

    def hash(self):
        return hash(tuple([self._label, *self._args]))

    STEP = None


Action.STEP = Action(Action.Label.FORWARD)


    STEP = None # Implement STEP!


class Canvas:
    """
    A rectangle on which elements can be drawn.
    """
    # TODO: Implement Canvas
    pass


class Text:
    """
    A TextBox that can be drawn on a canvas.
    """
    # TODO: Implement Text
    pass


def flatten():
    """
    Translates a Presentation process into a new process object, precomputing as much as possible.
    :return:
    """
    # TODO: Implement flatten
    pass


def present():
    """
    Plays a presentation on-screen.
    :return:
    """
    # TODO: Implement present.
    pass