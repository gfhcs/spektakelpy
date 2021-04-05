import abc


def cons(x, *ys):
    """
    A procedure that returns its arguments unaltered.
    :param x: An object.
    :param ys: A tuple of objects.
    :return: The pair (x, ys).
    """
    return x, ys



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