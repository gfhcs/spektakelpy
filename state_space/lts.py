from util import check_type


class State:
    """
    A state in a labelled transition system.
    """

    def __init__(self, content):
        """
        Creates a new LTS state.
        :param content: An object with which this state should be decorated.
        """
        self._content = content
        self._transitions = []

    def add_transition(self, t):
        """
        Adds a transition from this state to some other state.
        :param t: The transition to add.
        """
        if not isinstance(self._transitions, list):
            raise RuntimeError("This state has already been sealed and can therefor not be extended by more transitions!")
        self._transitions.append(check_type(t, Transition))

    def seal(self):
        """
        Makes this state immutable, i.e. prevents the addition of transitions originating from it.
        """
        self._transitions = tuple(self._transitions)

    @property
    def content(self):
        """
        The content that this state is decorated with.
        """
        return self._content

    @property
    def transitions(self):
        """
        The transitions originating from this state.
        :return: An iterable of Transition objects.
        """
        return tuple(self._transitions)


class Transition:
    """
    A directed, labelled edge leading into a target state in a labelled transition system.
    """
    def __init__(self, label, target):
        """
        Creates a new transition
        :param label: An object that labels this edge.
        :param target: The state this edge leads into.
        """
        self._label = label
        self._target = check_type(target, State)

    @property
    def label(self):
        """
        The object labelling this edge.
        """
        return self._label

    @property
    def target(self):
        """
        The state this edge leads into.
        """
        return self._target


class LTS:
    """
    An object of this type represents a "labelled transition system", i.e. a set of states that are interconnected by
    directed edges with labels.
    """

    def __init__(self, s0):
        """
        Creates a new LTS.
        :param s0: The initial state of this LTS.
        """

        super().__init__()
        self._s0 = s0

    @property
    def initial(self):
        """
        The initial state of this LTS.
        """
        return self._s0


def lts2str(lts):
    """
    Denotes an LTS by a string. This is mostly for debugging purposes.
    :param lts: The LTS to summarize in a string.
    :return: A string.
    """
    import io

    prefix = ""
    sidx = 0
    with io.StringIO() as output:
        agenda = [lts.initial]
        visited = {}
        while True:
            try:
                s = agenda.pop()
            except IndexError:
                return output.getvalue()

            try:
                v, sname = visited[id(s)]
                if v:
                    continue
            except KeyError:
                sname = f"state{sidx}"
                sidx += 1

            visited[id(s)] = (True, sname)

            for t in s.transitions:
                output.write(prefix)
                prefix = "\n"
                output.write(sname)
                output.write(" --")
                output.write(str(t.label))
                output.write("--> ")

                try:
                    _, tname = visited[id(t.target)]
                except KeyError:
                    tname = f"state{sidx}"
                    visited[id(t.target)] = (False, tname)
                    sidx += 1

                output.write(tname)
                agenda.append(t.target)


def state_space(transitions):
    """
    Assembles a set of transitions into a labelled-transition-system.
    :param transitions: An iterable of tuples (s, es), where es is an iterable of pairs (idx, s'), where idx is the index
     of the task in s the execution of which transforms s into s'. es comprises *all* pairs with this property.
    :return: An LTS object. The initial state of this LTS will be the origin of the very first transition enumerated
    in 'transitions'.
    """

    states = {}
    s0 = None

    for s, es in transitions:
        try:
            origin = states[s]
        except KeyError:
            origin = State(s)
            states[s] = origin
            if s0 is None:
                s0 = origin

        for idx, t in es:
            try:
                destination = states[t]
            except KeyError:
                destination = State(t)
                states[t] = destination

            origin.add_transition(Transition(idx, destination))

    # We're doing it here because not all states might be enumerated as origins (i.e. if they don't have outgoing
    # transitions).
    for s in states.values():
        s.seal()

    assert s0 is not None
    return LTS(s0)
