import abc
from core.compact import CompactObject


class State(CompactObject):
    """
    Defines the state of a process.
    """
    pass


class Interaction(CompactObject):
    """
    Defines an interaction with a process.
    """
    pass


class Process(abc.ABC):
    """
    An entity that defines how interactions with it make it transition from its current state into a new state.
    """

    @property
    @abc.abstractmethod
    def initial(self):
        """
        The initial state of this process.
        :return: A State object.
        """
        pass

    @abc.abstractmethod
    def transition(self, state, interaction):
        """
        Defines how this process is transitioning from the given state into a new state, in the course of the given
        interaction.
        This procedure is functional, i.e. equal inputs are going to lead to equal outputs.
        :param state: The State object from which the transition should originate.
        :param interaction: The Interaction object prompting the transition.
        :return: A State object.
        """
        pass