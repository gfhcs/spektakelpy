import abc


class Location:
    """
    A control flow location inside a spectacle, i.e. an object that determines which interactions or events the spectacle
    can react to next.
    """
    def __init__(self):
        pass


class Guard(abc.ABC):
    """
    A callable that decides if an edge inside a spectacle can be taken.
    """

    @abc.abstractmethod
    def decide(self, event, state):
        """
        Decides if the condition represented by this Guard is satisfied.
        :param state: The current state of the spectacle.
        :return: Either True or False.
        """
        pass

    def __call__(self, e, s):
        return self.decide(e, s)


class Update:
    """
    A callable that maps the current state of a spectacle to a new state.
    """

    @abc.abstractmethod
    def transform(self, event, state):
        """
        Computes the new state of the spectacle.
        :param state: The current state of the spectacle.
        :return: An object that represents the new state of the spectacle.
        """
        pass

    def __call__(self, e, s):
        return self.transform(e, s)


class Edge:
    """
    A control flow edge inside a spectacle, i.e. an object that defines a reaction of the spectacle to an interaction
    or event.
    """
    def __init__(self, t, guard, update, destination):
        """
        Creates a new control flow edge.
        :param t: A type object specifying which Event objects this edge is supposed to be followed for.
        :param destination: A Location object specifying which control location this edge is leading to.
        :param guard: A Guard object defining when this Edge can be followed.
        :param update: An Update object defining how the spectacle state is to be updated when this edge is followed.
        """
        self._destination = destination
        self._etype = t
        self._guard = guard
        self._update = update

    @property
    def event_type(self):
        """
        The type of event this edge is supposed to be followed for.
        :return: A type object that represents an Event subtype.
        """
        return self._etype

    @property
    def guard(self):
        """
        The condition under which this Edge can be followed.
        :return: A Guard object.
        """
        return self._guard

    def update(self):
        """
        The way the spectacle state is to be updated when this edge is followed.
        :return: An Update object.
        """
        return self._update

    @property
    def destination(self):
        """
        The control flow location this edge leads to.
        :return: A Location object.
        """
        return self._destination


class Spectacle:
    """
    A control flow graph that defines a set of possible appearance traces.
    """

    def __init__(self, l0, s0):
        """
        Creates a new spectacle.
        :param l0: A Location object that all appearance traces of this spectacle should start at.
        :param s0: An object that defines the initial state for all appearance traces of this spectacle.
        """
        self._l0 = l0
        self._s0 = s0

    @property
    def initial_location(self):
        """
        The control location at which all appearance traces described by this spectacle start.
        :return: A Location object.
        """
        return self._l0

    @property
    def initial_state(self):
        """
        The initial state for all appearance traces of this spectacle.
        :return: An object.
        """
        return self._s0
