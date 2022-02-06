from util import check_type
from .machine import MachineState
from util.lts import LTS, State, Transition


def explore(mstate, scheduler=None):
    """
    Enumerates the entire state space of a task machine.
    :param mstate: The MachineState object forming the root of the exploration.
    :param scheduler: A callable (s) -> ts, mapping MachineState s to an iterable ts of task ID objects, specifying
    which Tasks are eligible for being scheduled in state s. By default, *all* tasks are eligible in all states.
    :return: An iterable of tuples (s, es), where es is an iterable of pairs (tid, s'), where tid is a task ID object
    specifying a task execution of which transforms s into s'. es comprises *all* pairs with this property.
    The very first s enumerated by this method will be the initial state. es may be empty.
    """

    check_type(mstate, MachineState)

    if scheduler is None:
        def scheduler(s):
            return [ss.taskid for ss in s.task_states]

    visited = set()
    agenda = [mstate]

    while len(agenda) > 0:
        s = agenda.pop()
        if s in visited:
            continue
        es = []
        for tid in scheduler(s):
            ss = s.get_task_state(tid).run(s)
            es.append((tid, ss))
            agenda.append(ss)

        yield s, es
        visited.add(s)


def state_space(transitions):
    """
    Assembles a set of transitions into a labelled-transition-system.
    :param transitions: An iterable of tuples (s, es), where es is an iterable of pairs (tid, s'), where tid is a task
    ID object specifying a task execution of which transforms s into s'. es comprises *all* pairs with this property.
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

        for tid, t in es:
            try:
                destination = states[t]
            except KeyError:
                destination = State(t)
                states[t] = destination

            origin.add_transition(Transition(tid, destination))

    # We're doing it here because not all states might be enumerated as origins (i.e. if they don't have outgoing
    # transitions).
    for s in states.values():
        s.seal()

    assert s0 is not None
    return LTS(s0)
