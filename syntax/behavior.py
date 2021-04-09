
from core.process import Process
from util import check_type
from syntax.ast import BooleanExpression


class Location:
    """
    A control flow location, i.e. an object that determines which actions a process can perform next.
    """
    def __init__(self):
        """
        Creates a new control flow location.
        """

        self._edges = []

    def add_edge(self, e):
        """
        Adds an edge originating from this location.
        :param e: An Edge object.
        """

        if not isinstance(self._edges, list):
            raise RuntimeError("This location object has been sealed and thus no edges can be added anymore!")

        check_type(e, Edge)

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


class Action:
    pass


class Edge:
    """
    A control flow edge, i.e. an object that defines an action a process can perform.
    """
    def __init__(self, action, guard, update, destination):
        """
        Creates a new control flow edge.
        :param action: The Action that this edge defines.
        :param destination: A Location object specifying the control location this edge is leading to.
        :param guard: A BooleanExpression that determines in which states of the process this edge can be taken.
        :param update: An Update object defining how the state of the process is to be updated when this edge is followed.
        """

        self._destination = check_type(destination, Location)
        self._action = check_type(action, Action)
        self._guard = check_type(guard, BooleanExpression)
        self._update = check_type(update, Update)

    @property
    def action(self):
        """
        The action that this edge defines.
        :return: An Action object.
        """
        return self._action

    @property
    def guard(self):
        """
        The condition under which this Edge can be followed.
        :return: A BooleanExpression object.
        """
        return self._guard

    @property
    def update(self):
        """
        The way the process state is to be updated when this edge is followed.
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


class Update:
    """
    A set of assignments that modify the state of a process.
    """

    def __init__(self, assignments):
        """
        Creates a new update.
        :param assignments: The assignments that define the update to be constructed.
        """
        super().__init__()

        self._assignments = set(assignments)

    def __len__(self):
        return self._assignments

    def __iter__(self):
        return iter(self._assignments)

    def __contains__(self, item):
        return item in self._assignments


class SymbolicProcess(Process):
    """
    A process the behavior of which is defined by a nested, labelled transition system over variables (VLTS).
    The external behavior of the process is defined as 1 control flow graph of locations and decorated edges.
    Internally, the process may contain further child processes that it controls.
    The state of a symbolic process comprises the states of all its subprocesses.
    """

    def __init__(self, l0, children):
        """
        Creates a new symbolic process.
        :param l0:
        :param children: The child processes that this process controls.
        """

        super().__init__()

        check_type(l0, Location)
        children = list(children)
        for c in children:
            check_type(c, SymbolicProcess)

        self._l0 = l0
        self._children = children

    @property
    def initial_location(self):
        """
        The initial control location for the external behavior of this process.
        :return: A Location object.
        """
        return self._l0

    @property
    def initial(self):
        # TODO: This is composed of the initial states of the children, plus the global variables that this parent
        # process defines. All these values should be composed into one single Value object.
        # Don't forget to also encode the control locations!
        raise NotImplementedError()

    def transition(self, state, interaction):
        pass


