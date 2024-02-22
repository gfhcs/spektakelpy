import itertools
import random

from state_space.lts import LTS, State, Transition


def reach_sbisim(state, label):
    """
    Enumerates all states that are reachable from the given state by following exactly one transition with the given
    label. Note that this may apply to multiple transitions!
    Using this procedure as the 'reachable' parameter in 'coarsest' will make it produce a strong bisimulation.
    :param state: An LTS state.
    :param label: A transition label.
    """
    assert isinstance(state, State)
    for t in state.transitions:
        if t.label == label:
            yield t.target


def reach_wbisim(state, label):
    """
    Enumerates all states that are reachable from the given state by following a sequence of transition labels, subject
    to the following conditions.
        1. The sequence may have any finite length.
        2. If the given label is None, the sequence must not contain labelled transitions.
        3. If the given label is not None, the sequence must contain exactly one labelled transition, the label of
           which must be the given one.
    Using this procedure as the 'reachable' parameter in 'coarsest' will make it produce a weak bisimulation.
    :param state: An LTS state.
    :param label: A transition label.
    """
    assert isinstance(state, State)

    agenda = [(state, False)]
    reached = set()

    while len(agenda) > 0:
        s, seen_label = agenda.pop()

        if s in reached:
            continue
        reached.add(s)

        if label is None or seen_label:
            yield s

        for t in s.transitions:
            if t.label is None or (label is not None and (t.label == label and not seen_label)):
                agenda.append((t.target, seen_label | (t.label is not None)))


def reach_ocong(state, label):
    """
    Enumerates all states that are reachable from the given state by following a sequence of transition labels, subject
    to the following conditions.
        1. The sequence must have nonzero length.
        2. If the given label is None, the sequence must not contain labelled transitions.
        3. If the given label is not None, the sequence must contain exactly one labelled transition, the label of
           which must be the given one.
    Using this procedure as the 'reachable' parameter in 'coarsest' will make it produce a observational
    congruence bisimulation. It is very similar to weak bisimulation, but states cannot emulate internal actions by
    a zero-transition trace.
    :param state: An LTS state.
    :param label: A transition label.
    """
    state_has_internal_loop = any(t.target is state and t.label is None for t in state.transitions)
    for s in reach_wbisim(state, label):
        if label is not None or s is not state or state_has_internal_loop:
            yield s


def reach_cached(reachable):
    """
    This procedure caches the results of another reachability procedure, for faster repeated retrieval. It is supposed
    to be used as a wrapper around functions that can be used for the 'reachable' parameter of 'coarsest'.
    :param reachable: A procedure that can be used for the 'reachable' parameter of 'coarsest'.
    :return: A procedure that can be used for the 'reachable' parameter of 'coarsest'. Note that extensive use of this
             procedure may allocate considerable amounts of memory, which will only be freed once the procedure is
             deleted.
    """

    cache = dict()

    def cached(state, label):
        key = (state, label)
        try:
            return cache[key]
        except KeyError:
            rs = list(reachable(state, label))
            cache[key] = rs
            return rs

    return cached


def refine(relation, reachable):
    """
    Computes the coarsest subset of an equivalence relation over LTS states that is a bisimulation according
    to the given reachability predicate.
    This procedure ignores state content.
    :param relation: A list of lists of states, encoding a partitioning of a state set into equivalence classes.
                     This list will be modified in place!
    :param reachable: A procedure that accepts a state and a transition label as arguments and enumerates all the states
                      that are considered 'reachable' from the given state, emulating the given transition label.
                      It is up to the caller to decide on the exact meaning of "emulating". The caller can use this
                      parameter to select strong bisimilarity, observational congruence, or weak bisimilarity.
    """

    class RefinedException(Exception):
        pass

    # We randomize the order in which we iterate over sets, hoping to find good splitters more quickly:
    def permute(l):
        return random.sample(l, k=len(l))

    s2p = {state: partition for partition in relation for state in partition}

    while True:
        try:
            for pidx, p in permute(list(enumerate(relation))):
                if len(p) == 1:
                    continue
                for s in permute(p):
                    assert isinstance(s, State)
                    for t in permute(s.transitions):
                        assert isinstance(t, Transition)
                        pt = s2p[t.target]
                        pos, neg = [], []

                        for ss in permute(p):
                            if any((s2p[tt] is pt) for tt in reachable(ss, t.label)):
                                pos.append(ss)
                            else:
                                neg.append(ss)

                        if len(pos) * len(neg) > 0:
                            relation.pop(pidx)
                            relation.insert(pidx, neg)
                            relation.insert(pidx, pos)
                            for state in pos:
                                s2p[state] = pos
                            for state in neg:
                                s2p[state] = neg
                            raise RefinedException()

            # TODO: Have this procedure *yield* every time a partition gets split! This is useful for callers who might want to stop early!

        except RefinedException:
            continue
        else:
            return


def bisimulation(reachable, *ltss):
    """
    Computes the coarsest equivalence relation on the states of multiple LTSs that is a bisimulation according
    to the given reachability predicate.
    This procedure does take state content into account!
    :param ltss: A number of LTSs.
    :param reachable: A procedure that accepts a state and a transition label as arguments and enumerates all the states
                      that are considered 'reachable' from the given state, emulating the given transition label.
                      It is up to the caller to decide on the exact meaning of "emulating". The caller can use this
                      parameter to select strong bisimilarity, observational congruence, or weak bisimilarity.
    :return: A list of lists of states, encoding a partitioning of the set of all states in all LTSs
             set into equivalence classes.
    """

    # TODO: Factor out an iterator over all the states of an LTS and use it everywhere!

    # Create an initial partitioning, by state content:
    relation = dict()
    agenda = [lts.initial for lts in ltss]
    reached = set()
    while len(agenda) > 0:
        s = agenda.pop()
        if s in reached:
            continue
        reached.add(s)

        try:
            partition = relation[s.content]
        except KeyError:
            partition = []
            relation[s.content] = partition

        partition.append(s)

        for t in s.transitions:
            agenda.append(t.target)
    del reached

    relation = list(relation.values())
    refine(relation, reachable)
    # TODO: After every subdivision that is yielded by 'refine' (see TODO above),
    # check if one of the given LTS is missing in that subdivision. If so, raise an exception
    # indicating that there is no equivalence relation.
    return relation


def reduce(lts, reachable, remove_internal_loops=False):
    """
    Computes a smaller LTS, that is equivalent to the given one under the specified bisimilarity.
    :param lts: The LTS that is to be reduced.
    :param reachable: A procedure that accepts a state and a transition label as arguments and enumerates all the states
                      that are considered 'reachable' from the given state, emulating the given transition label.
                      It is up to the caller to decide on the exact meaning of "emulating". The caller can use this
                      parameter to select strong bisimilarity, observational congruence, or weak bisimilarity.
    :param remove_internal_loops: Specifies if the resulting LTS should not contain any internal transitions leading
                                  from a state back into the same state.
    :return: An LTS.
    """

    partitions = bisimulation(reachable, lts)
    states = [State(p[0].content) for p in partitions]

    s2idx = {s: idx for idx, partition in enumerate(partitions) for s in partition}

    for state, partition in zip(states, partitions):
        for label, tidx in {(t.label, s2idx[t.target]) for s in partition for t in s.transitions}:
            if not (remove_internal_loops and state is states[tidx]):
                state.add_transition(Transition(label, states[tidx]))

    return LTS(states[s2idx[lts.initial]].seal())


# TODO: The test suite should *test* isomorphic, but not use it to inspect results,
#  as it is building on the thing we want to test!
def isomorphic(lts1, lts2):

    # First traverse both LTS's, collecting all states and counting transitions:
    states, nts = [], []
    for lts in (lts1, lts2):
        agenda = [lts.initial]
        reached = set()
        num_transitions = 0
        while len(agenda) > 0:
            s = agenda.pop()
            if s in reached:
                continue
            reached.add(s)
            num_transitions += len(s.transitions)
            agenda.extend((t.target for t in s.transitions))
        states.append(reached)
        nts.append(num_transitions)

    states1, states2 = states
    num_transitions1, num_transitions2 = nts
    if len(states1) != len(states2) or num_transitions1 != num_transitions2:
        return False
    del states, nts, num_transitions1, num_transitions2

    # Now get a strong bisimilarity relation as a start:
    relation = bisimulation(reach_sbisim, lts1, lts2)

    # We now enumerate all possible ways of refining the relation into a bijection between the LTSs:
    left, pright = [], []
    for partition in relation:
        p1, p2 = [], []
        for s in partition:
            (p1 if s in states1 else p2).append(s)
        if len(p1) != len(p2):
            # Gereon suspects that if this case never arises, we can already safely conclude that the LTSs are
            # in fact isomorphic, i.e. that there must be *some* bijection that works.
            return False
        left.extend(p1)
        pright.append(itertools.permutations(p2))

    class InvalidBijection(Exception):
        pass

    for permutation in itertools.product(*pright):
        # Check if the bijection arising from this permutation fulfills the requirements of isomorphy:
        bijection = {l: (l, r) for l, r in zip(left, itertools.chain(*permutation))}
        try:
            for l, r in bijection.values():
                if len(l.transitions) != len(r.transitions):
                    raise InvalidBijection()
                for tl in l.transitions:
                    if not any(tl.label == tr.label and bijection[tl.target][1] is tr.target for tr in r.transitions):
                        raise InvalidBijection()
        except InvalidBijection:
            continue
        else:
            return True

    return False
