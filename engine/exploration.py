from engine.core.interaction import InteractionState, Interaction
from engine.core.machine import MachineState
from util import check_type


def schedule_all(s):
    """
    A scheduler function allowing *any* enabled transitions (except for Interaction.NEVER).
    This is the most basic scheduler.
    :param s: A MachineState object.
    :return: An iterable of indices, specifying which Task objects in s.task_states are eligible for being scheduled.
    """
    return tuple(idx for idx, ss in enumerate(s.task_states) if ss.enabled(s) if not (isinstance(ss, InteractionState) and ss.interaction == Interaction.NEVER))


def schedule_nonzeno(s):
    """
    A scheduler function that partially resolves nondeterminism, by the following rules:
    1. If an internal action is scheduled, only one action is scheduled.
    2. Interaction tasks will only be scheduled in states that do not enable any internal actions.
    3. The NEVER interaction is ignored.
    :param s: A MachineState object.
    :return: An iterable of indices, specifying which Task objects in s.task_states are eligible for being scheduled.
    """

    idx_internal = None
    idx_interaction = []

    for idx, ss in enumerate(s.task_states):
        if not ss.enabled(s):
            continue
        if isinstance(ss, InteractionState):
            if ss.interaction == Interaction.NEVER:
                continue
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
    :param mstate: The MachineState object forming the root of the state_space.
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
        # print(len(agenda), len(visited))
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


