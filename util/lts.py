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
