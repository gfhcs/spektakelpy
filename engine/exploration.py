from util import check_type
from .machine import MachineState


def explore(mstate, scheduler=None):
    """
    Enumerates the entire state space of a task machine.
    :param mstate: The MachineState object forming the root of the exploration.
    :param scheduler: A callable (s) -> ts, mapping MachineState s to an iterable ts of TaskState objects belonging to s
    that specifies which Tasks are eligible for being scheduled in state s. By default, *all* tasks are eligible in
    all states.
    :return: An iterable of tuples (s, es), where es is an iterable of pairs (t, s'), where t is a TaskState that is
    part of MachineState s, execution of which leads to MachineState s'. es comprises *all* pairs with this
    property.
    """

    check_type(mstate, MachineState)

    if scheduler is None:
        def scheduler(s):
            return s.tasks

    visited = set()
    agenda = [mstate]

    while len(agenda) > 0:
        s = agenda.pop()
        if s in visited:
            continue
        es = []
        for t in scheduler(s):
            ss = t.execute()
            es.append((t, ss))
            agenda.append(ss)

        yield s, es
        visited.add(s)


def state_space(transitions):
    """
    Assembles a set of transitions into a labelled-transition-system.
    :param transitions: An iterable of tuples (s, es), where es is an iterable of pairs (t, s'), where t is a TaskState
    that is part of MachineState s, execution of which leads to MachineState s'. es comprises *all* pairs with this
    property.
    :return: An LTS object.
    """
    raise NotImplementedError()