import abc


def cons(x, *ys):
    """
    A procedure that returns its arguments unaltered.
    :param x: An object.
    :param ys: A tuple of objects.
    :return: The pair (x, ys).
    """
    return x, ys


class Location:
    """
    A control flow location inside a spectacle, i.e. an object that determines which interactions or events the spectacle
    can react to next.
    """
    def __init__(self, inner=(), compose=cons):
        """
        Creates a new control flow location.
        :param inner: An iterable of spectacle objects that are supposed to take place while the outer spectacle
                      rests in the new location.
        :param compose: A procedure that takes as arguments a state x and a state tuple ys and returns a state object.
                        This procedure defines how the local state information and the states of the inner spectacles
                        are combined into the state of the spectacle.
        """
        self._inner = tuple(inner)

        for i in self._inner:
            if not isinstance(i, Spectacle):
                raise TypeError("'inner' must contain only Spectacle objects!")

        self._compose = compose
        self._edges = []

    def add_edge(self, e):
        """
        Adds an edge originating from this location.
        :param e: An Edge object.
        """

        if not isinstance(self._edges, list):
            raise RuntimeError("This location object has been sealed and thus no edges can be added anymore!")

        if not isinstance(e, Edge):
            raise TypeError("'e' must be of type Edge!")

        self._edges.append(e)

    def seal(self):
        """
        Makes this Location immutable, i.e. prevents the addition of further edges.
        """
        self._edges = tuple(self._edges)

    @property
    def edges(self):
        """
        The edges originating from this location.
        :return: An iterable of Edge objects.
        """
        return tuple(self._edges)

    @property
    def spectacles(self):
        """
        The inner spectacles that take place while the outer spectacle rests in this location.
        :return: An iterable of Spectacles.
        """
        return self._inner

    @property
    def compose(self, local_state, *inner_states):
        """
        Maps the states of the inner spectacles of this location to the state of the outer spectacle.
        :param local_state: The private state of the spectacle.
        :param inner_states: The tuple of states that the inner spectacles of this location are in.
        :return: The state of the outer spectacle.
        """
        if len(inner_states) != len(self._inner):
            raise ValueError("Expected {e} inner states, but got {f}!".format(e=len(self._inner), f=len(inner_states)))
        return self._compose(local_state, *inner_states)


class Guard(abc.ABC):
    """
    A callable that decides if an edge inside a spectacle can be taken.
    """

    @abc.abstractmethod
    def decide(self, state, event):
        """
        Decides if the condition represented by this Guard is satisfied.
        :param state: The current state of the spectacle.
        :param event: The event that occurred.
        :return: Either True or False.
        """
        pass

    def __call__(self, s, e):
        return self.decide(s, e)


class Update:
    """
    A callable that maps the current state of a spectacle to a new state.
    """

    @abc.abstractmethod
    def transform(self, state, event):
        """
        Computes the new state of the spectacle.
        :param state: The current state of the spectacle.
        :param event: The event that occurred.
        :return: An object that represents the new state of the spectacle.
        """
        pass

    def __call__(self, s, e):
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
    def initial_local_state(self):
        """
        The initial (local) state for all appearance traces of this spectacle.
        :return: An object.
        """
        return self._s0

def iter_locations(s):
    """
    Iterates over the control locations of a spectacle. Every location is enumerated exactly once.
    :param s: A Spectacle object.
    :return: An iterable of locations.
    """
    handled = set()
    agenda = []
    while len(agenda) > 0:
        l = agenda.pop()
        if l in handled:
            continue
        yield l
        handled.add(l)
        for e in l.edges:
            agenda.append(e.destination)

class ControlTree:
    """
    Represents a set of control locations that the sub spectacles of a spectacle are resting in.
    """

    def __init__(self, s, l, *cs):
        """
        Creates a new ControlTree.
        :param s: The Spectacle for which this control tree is constructed.
        :param l: The Location the spectacle this control tree belongs to is resting in.
        :param cs: The children of this tree, i.e. the control trees belonging to the inner
                    spectacles of the current location.
        """

        if not isinstance(s, Spectacle):
            raise TypeError("'s' must be of type Spectacle!")

        if not isinstance(l, Location):
            raise TypeError("'l' must be of type Location!")

        for t in cs:
            if not isinstance(t, ControlTree):
                raise TypeError("All objects in 'cs' must be of type ControlTree!")

        if l not in iter_locations(s):
            raise ValueError("The given location is not part of the given spectacle!")

        if len(cs) != len(l.spectacles):
            raise ValueError("The control tree for this location must contain {e} child trees!".format(e=len(l.spectacles)))

        for ss, ct in zip(l.spectacles, cs):
            if ss is not ct.spectacle:
                raise ValueError("The children of this control tree must belong to the inner spectacles of the given location!")

        self._s = s
        self._l = l
        self._cs = cs

    @property
    def spectacle(self):
        """
        The spectacle for which this control tree is valid.
        :return: A Spectacle object.
        """
        return self._s

    @property
    def location(self):
        """
        The control location that the spectacle this tree belongs to is resting in.
        :return: A Location object.
        """
        return self._l

    @property
    def children(self):
        """
        The children of this tree, i.e. the control trees belonging to the inner spectacles of the current location.
        :return: An iterable of ControlTree objects.
        """
        return self._cs


def initialize(s):
    """
    Computes the initial control tree and initial state of a spectacle.
    :param s: A Spectacle object.
    :return: A pair (c, s) where c is a ControlTree object and s is a state.
    """
    css = tuple(map(initialize, s.initial_location.spectacles))
    c = ControlTree(s, s.initial_location, *[cs[0] for cs in css])
    s = s.initial_location.compose(s.initial_local_state, *[cs[1] for cs in css])
    return c, s


def step(c, s, e):
    """
    Transforms the control tree and state of a spectacle according to an event that occurred.
    :param c: A ControlTree object.
    :param s: A state object.
    :param e: An Event.
    :return: A pair (nc, ns) consisting of a ControlTree nc and a state object ns that represent the state of the
             spectacle after the given event.
    """

    for edge in c.location:
        if isinstance(e, edge.event_type):
            if edge.guard(s, e):
                nl = edge.destination
                nc = edge.update(s, e)
                return nl, ns