import abc


class Event(abc.ABC):
    """
    Events occur during a spectacle. They can be caused by the presenter, the audience or by technical sources.
    """
    pass

class TickEvent(Event):
    """
    This event occurs whenever a quantum of time goes by.
    """
    pass

class ForwardEvent(Event):
    """
    This event occurs when the presenter triggers a step forward in the spectacle.
    """
    pass


class BackwardEvent(Event):
    """
    This event occurs when the presenter triggers a step back in the spectacle.
    """
    pass


class ChoiceEvent(Event):
    """
    This event occurs when the presenter selects one of several enabled alternatives.
    """
    def __init__(self, choice):
        """
        Creates a new choice event.
        :param choice: The choice that was taken.
        """
        super().__init__()
        self._c = choice

    @property
    def choice(self):
        """
        The choice that was taken.
        """
        return self._c

