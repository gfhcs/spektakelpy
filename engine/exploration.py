from util import check_type
from .machine import MachineState
from util.lts import LTS, State, Transition
from .tasks.interaction import InteractionState


def schedule_all(s):
    """
    A scheduler function allowing *any* enabled transitions. This is the most simple scheduler.
    :param s: A MachineState object.
    :return: An iterable of indices, specifying which Task objects in s.task_states are eligible for being scheduled.
    """
    return tuple(idx for idx, ss in enumerate(s.task_states) if ss.enabled(s))


def schedule_nonzeno(s):
    """
    A scheduler function that partially resolves nondeterminism, by the following rules:
    1. If an internal action is scheduled, only one action is scheduled.
    2. Interaction tasks will only be scheduled in states that do not enable any internal actions.
    :param s: A MachineState object.
    :return: An iterable of indices, specifying which Task objects in s.task_states are eligible for being scheduled.
    """

    idx_internal = None
    idx_interaction = []

    for idx, ss in enumerate(s.task_states):
        if not ss.enabled(s):
            continue
        if isinstance(ss, InteractionState):
            idx_interaction.append(idx)
        elif idx_internal is None or idx < idx_internal:
            idx_internal = idx

    if idx_internal is None:
        return idx_interaction
    else:
        return [idx_internal]


def explore(mstate, scheduler=schedule_all):
    """
    Enumerates the entire state space of a task machine.
    :param mstate: The MachineState object forming the root of the exploration.
    :param scheduler: A callable (s) -> ts, mapping MachineState s to an iterable ts of task ID objects, specifying
    which Tasks are eligible for being scheduled in state s. By default, *all* tasks are eligible in all states.
    :return: An iterable of tuples (s, es), where es is an iterable of pairs (idx, s'), where idx is the index of the
    task in s the execution of which transforms MachineState s into MachineState s'. s and s' are sealed.
    es comprises *all* pairs with this property.
    The very first s enumerated by this method will be the initial state. es may be empty.
    """

    check_type(mstate, MachineState)

    if not mstate.sealed:
        mstate = mstate.clone_unsealed()
        mstate.seal()

    visited = set()
    agenda = [mstate]

    while len(agenda) > 0:
        s = agenda.pop()
        if s in visited:
            continue
        es = []
        for idx in scheduler(s):
            ss = s.clone_unsealed()
            ss.task_states[idx].run(ss)
            ss.seal()
            es.append((idx, ss))
            agenda.append(ss)

        yield s, es
        visited.add(s)


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
