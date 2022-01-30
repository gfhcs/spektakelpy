
import itertools
from enum import Enum

from legacy.core.process import Process
from engine.state import Variable, Valuation
from util import check_type
from lang import OwnershipError


class Location:
    """
    A control flow location, i.e. an object that determines which actions a process can perform next.
    """
    def __init__(self):
        """
        Creates a new control flow location.
        """

        self._edges = []
        self._graph = None

    def add_edge(self, e):
        """
        Adds an edge originating from this location.
        :param e: An Edge object.
        """

        if self._graph is not None:
            raise OwnershipError("This location is already part of a graph and thus cannot be modified anymore!")

        check_type(e, Edge)
        e.own(self)
        self._edges.append(e)

    def own(self, graph):
        """
        Makes this location a component of the given graph. A location can be owned by only one graph.
        A location that is owned cannot be modified anymore.
        :param graph: The graph that is to own this location.
        """

        if self._graph is not None:
            raise OwnershipError("This location is already owned by a graph and thus cannot be owned again!")

        self._graph = check_type(graph, Graph)
        self._edges = tuple(self._edges)

    @property
    def owner(self):
        """
        A Graph object that this location is part of.
        :return: A Graph object.
        """
        return self._graph

    @property
    def edges(self):
        """
        The edges originating from this location.
        :return: An iterable of Edge objects.
        """
        return tuple(self._edges)


class Action:
    """
    A symbol identifying a type of action.
    """

    def __init__(self, label):
        """
        Creates a new action.
        :param label: The label for this action (a string).
        """
        super().__init__()

        self._label = label

    @property
    def label(self):
        """
        The label for this action.
        :return: A string.
        """
        return self._label


class SyncMode(Enum):
    """
    Defines the way that an edge is to be synchronized with edges of parallel processes.
    """
    SILENT = 0  # This action is always enabled, for the process to make a transition alone.
    TOINNER = 1  # Action must be synchronized with direct child processes that contain the FROMPARENT version of the action in their alphabet.
    FROMOUTER = 2  # Action must be synchronized with any direct parent process that contains the TOCHILDREN version of the action in their alphabet.
    PARALLEL = 3  # Action must be synchronized with all parallel processes that contain the PARALLEL version of the action in their alphabet.


class Edge:
    """
    A control flow edge, i.e. an object that defines an action a process can perform.
    """
    def __init__(self, action, syncmode, guard, update, destination):
        """
        Creates a new control flow edge.
        :param action: The Action that this edge defines.
        :param destination: A Location object specifying the control location this edge is leading to.
        :param syncmode: Specifies the way in which the action defined by this edge is to be synchronized with actions
                         from other processes.
        :param guard: A BooleanExpression that determines in which states of the process this edge can be taken.
        :param update: An Update object defining how the state of the process is to be updated when this edge is
                       followed.
        """

        self._destination = check_type(destination, Location)
        self._action = check_type(action, Action)
        self._guard = check_type(guard, BooleanExpression)
        self._update = check_type(update, Update)
        self._origin = None
        self._syncmode = check_type(syncmode, SyncMode)

    def own(self, origin):
        """
        Registers the given location as the origin (and thus owner) of this edge.
        :param origin: The location that is to be the origin of this edge.
        """

        if self._origin is not None:
            raise OwnershipError("This edge is already owned by a location and thus cannot be owned again!")

        self._origin = origin

    @property
    def origin(self):
        """
        A Location object that this edge originates from.
        :return: A Location object.
        """
        return self._origin

    @property
    def action(self):
        """
        The action that this edge defines.
        :return: An Action object.
        """
        return self._action

    @property
    def syncmode(self):
        """
        The way in which the action defined by this edge is to be synchronized actions from other processes.
        """
        return self._syncmode

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

        self._assignments = list(check_type(a, Assignment) for a in assignments)

    def __len__(self):
        return self._assignments

    def __iter__(self):
        return iter(self._assignments)


class Graph:
    """
    A graph of control flow locations and control flow edges that encodes the behavior of a (sub-) process.
    """

    def __init__(self, l0):
        """
        Creates a new process graph.
        :param l0: The initial control flow location of this graph.
        """
        super().__init__()
        self._l0 = check_type(l0, Location)

        # Own all the locations in the given graph:
        ls = set()
        agenda = {l0}
        while len(agenda) > 0:
            l = agenda.pop(0)
            l.own(self)
            ls.add(l)
            for e in l.edges:
                ll = e.destination
                if ll.owner is None:
                    agenda.add(ll)

        self._locations = frozenset(ls)
        self._alphabet = None
        self._alphabet_fromouter = None
        self._alphabet_parallel = None
        self._variables = None

    @property
    def locations(self):
        """
        A set of all the locations in this graph.
        """
        return self._locations

    @property
    def alphabet(self):
        """
        An iterable of all the action labels that are contained in this graph.
        """
        if self._alphabet is None:
            self._alphabet = frozenset(e.action for l in self.locations for e in l.edges)

        return self._alphabet

    @property
    def alphabet_fromouter(self):
        """
        An iterable of all the action labels that occur with syncmode FROMOUTER in this graph.
        """
        if self._alphabet_fromouter is None:
            self._alphabet_fromouter = frozenset(e.action for l in self.locations for e in l.edges if e.sync_mode == SyncMode.FROMOUTER)

        return self._alphabet_fromouter

    @property
    def alphabet_parallel(self):
        """
        An iterable of all the action labels that occur with syncmode PARALLEL in this graph.
        """
        if self._alphabet_parallel is None:
            self._alphabet_parallel = frozenset(e.action for l in self.locations for e in l.edges if e.sync_mode == SyncMode.PARALLEL)

        return self._alphabet_parallel

    @property
    def variables(self):
        """
        An iterable of all the variables that are referenced in this graph.
        """
        if self._variables is None:
            vs = set()
            for l in self.locations:
                for e in l.edges:
                    vs |= e.guard.variables
                    vs |= e.update.variables
            self._variables = frozenset(vs)

        return self._variables

    @property
    def initial_location(self):
        """
        The initial control flow location of this graph.
        :return: A Location object.
        """
        return self._l0


class SymbolicProcess(Process):
    """
    A process the behavior of which is defined by a nested, labelled transition system over variables (VLTS).
    The external behavior of the process is defined by a tuple of control flow graphs that operate in parallel.
    Internally, the process may contain further child processes that it controls.
    The state of a symbolic process comprises the states of all its subprocesses.
    """

    def __init__(self, variables, graphs, children):
        """
        Creates a new symbolic process.
        :param variables: The variables defined on the root level of this symbolic process.
        :param graphs: The control flow graphs the parallel composition of which define the external behavior of this process.
        :param children: A dict mapping identifiers to child processes that this process controls internally.
        """
        super().__init__()

        self._members = {}
        for v in variables:
            check_type(v, Variable)
            if v.name in self._members.keys():
                raise ValueError("There must not be two member variables with the same name!")
            v.own(self)
            self._members[v.name] = v

        self._behavior = tuple(check_type(g, Graph) for g in graphs)
        self._alphabet_fromouter = frozenset(a for g in graphs for a in g.alphabet_from_outer)

        for k, c in children.items():
            check_type(c, SymbolicProcess)
            if k in self._members.keys():
                raise ValueError("The name '{}' was specified for at least one child process and at the same time"
                                 " for another child process or variable, which is illegal.".format(k))
            self._members[k] = c


    @property
    def alphabet_fromouter(self):
        """
        The set of actions for which this symbolic process contains a root-level edge with sync mode FROMOUTER.
        """
        return self._alphabet_fromouter

    def lookup_member(self, identifier):
        """
        Retrieves a member variable or direct child process by name.
        :param identifier: The name of the variable or child process to retrieve.
        :return: Either a Variable object, or a SymbolicProcess object.
        """
        return self._members[identifier]

    @property
    def variables(self):
        """
        The member variables of this process, i.e. the variables that are *directly* owned by this process.
        This does not include member variables owned by subprocesses.
        :return: A tuple of Variable objects.
        """
        return tuple(m for m in self._members.values() if isinstance(m, Variable))

    @property
    def behavior(self):
        """
        A tuple of control flow graphs that define the external behavior of this symbolic process.
        :return: A tuple of Graph objects.
        """
        return self._behavior

    @property
    def children(self):
        """
        The internal child processes that this process controls
        :return: A dict mapping identifiers to child processes
        """
        return {k: m for k, m in self._members.items() if isinstance(m, SymbolicProcess)}

    @property
    def initial(self):

        sub = [c.initial for c in self.children.values()]

        locations = {g: l for s in sub for g, l in s[0].items()}
        valuation = {var: val for s in sub for var, val in s[1]}

        for v in self.variables:
            valuation[v] = v.dtype.default

        for g in self._behavior:
            locations[g] = g.initial_location

        return locations, Valuation(valuation)

    def get_enabled(self, locations, valuation, action, sync_mode):
        """
        Computes the set of edges that this process is able to follow in the current state.
        This involves evaluating edge guards and resolving synchronization.
        :param locations: A dict mapping all the graphs of this process to their current target locations.
        :param valuation: A Dict object mapping the variables of the subproceses of this process to their current values.
        :param action: The action that is to be executed. If 'None' is given, *all* actions will be considered.
        :param sync_mode: The way that the given action is to be synchronized with the edges of this process.
        :return: An iterable of tuples of Edge objects. Each tuple contains a root-level edge as its first component.
                 The remaining components may be part of any subprocess of this process and are to be executed synchronously.
        """

        if sync_mode == SyncMode.SILENT:

            edges_parallel = {}

            for g in self._behavior:
                l = locations[g]
                for e in l.edges:
                    if action is None or e.action == action:
                        if e.sync_mode == SyncMode.SILENT and e.guard.evaluate(valuation):
                            yield e
                        elif e.sync_mode == SyncMode.PARALLEL and e.guard.evaluate(valuation):
                            try:
                                edges_parallel[e.action][g].append(e)
                            except KeyError:
                                edges_parallel[e.action] = {gg: ([e] if gg is g else []) for gg in self._behavior if e.action in gg.alphabet_parallel}
                        elif e.sync_mode == SyncMode.TOINNER and e.guard.evaluate(valuation):
                            for c in self.children.values():
                                if action in c.alphabet:
                                    for sedges in c.get_enabled(locations, valuation, e.action, SyncMode.TOINNER):
                                        yield (e, *sedges)

            for a, edges in edges_parallel.items():
                for sedges in itertools.product(edges.values()):
                    yield sedges

        elif sync_mode == SyncMode.TOINNER:
            for g in self._behavior:
                l = locations[g]
                for e in l.edges:
                    if e.action == action and e.sync_mode == SyncMode.FROMOUTER and e.guard.evaluate(valuation):
                        yield e
        elif sync_mode == SyncMode.FROMOUTER:
            raise ValueError("The sync_mode {} is invalid for this call!".format(sync_mode))
        elif sync_mode == SyncMode.PARALLEL:
            raise ValueError("The sync_mode {} cannot be used to synchronize "
                             "external actions with internal actions!".format(sync_mode))
        else:
            raise NotImplementedError("The sync_mode {} has not been implemented yet!".format(sync_mode))


    @staticmethod
    def transform(locations, valuation, *sedges):
        """
        Transforms a state of this process into a new state, by synchronously following a tuple of edges.
        This method ignores guards and synchronization semantics.
        :param locations: A dict mapping all the graphs of this process to their current target locations.
        :param valuation: A Dict object mapping the variables of the subproceses of this process to their current values.
        :param sedges: A tuple of edges that are to be executed synchronously.
        :return: A pair (locations, valuation).
        """

        valuation_out = dict(valuation)
        locations_out = dict(locations)
        written = set()
        for e in sedges:
            locations_out[e.owner.owner] = e.destination
            for var, exp in e.update:
                if var in written:
                    raise RuntimeError("The variable {v} is written by more than one of the given edges!".format(v=var))
                written.add(var)
                val = exp.evaluate(valuation)
                valuation_out[var] = val

        return locations_out, Valuation(valuation_out)

    def step(self, locations, valuation, action):
        """
        Computes a set of followup states of this process.
        :param locations: A dict mapping the subprocesses of this process to their current target locations.
        :param valuation: A Dict object mapping the variables of the subprocesses of this process to their current values.
        :param action: The action that is to be executed.
        :return: An iterable of pairs (locations, valuation) that represent the nondeterministically available follup states.
        """
        for sedges in self.get_enabled(locations, valuation, action):
            yield SymbolicProcess.transform(locations, valuation, *sedges)

    def transition(self, state, action):
        locations, valuation = state
        return self.step(locations, valuation, action)



