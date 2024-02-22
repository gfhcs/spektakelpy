import unittest

from state_space.equivalence import reduce, reach_wbisim, reach_sbisim, reach_ocong, reach_cached, isomorphic
from state_space.lts import State, LTS, Transition


class TestBisimilarity(unittest.TestCase):
    """
    This class contains test cases for our bisimilarity utility procedures.
    """

    def examine_example(self, lts_in, reachable, reduced_expected, remove_internal_loops):
        """
        Reduces an LTS according to some bismilarity definition and compares the result to the expected one.
        :param lts_in: The LTS to reduce.
        :param reachable: The 'reachable' procedure to use, defining the type of bisimilarity according to which
                          the LTS is to be reduced.
        :param reduced_expected: The LTS that we expect the reduction result to be isomorphic to.
        :param remove_internal_loops: Specifies if the resulting LTS should not contain any internal transitions leading
                                  from a state back into the same state.

        """

        lts_out = reduce(lts_in, reach_cached(reachable), remove_internal_loops=remove_internal_loops)
        self.assertTrue(isomorphic(lts_out, reduced_expected))

    def examine_multiple(self, lts_in, *r2e):
        """
        Reduces an LTS according to multiple bisimilarity definitions and compares results to expectations.
        :param lts_in: The LTS to reduce.
        :param r2e: An iterable of pairs (reachable, remove_internal_loops, reduced_expected), to be used for calling self.examine_example.
        """

        r2s = {id(reach_wbisim): "weak",
               id(reach_sbisim): "strong",
               id(reach_ocong): "ocong"}

        for reachable, remove_internal_loops, reduced_expected in r2e:
            with self.subTest(type=r2s[id(reachable)]):
                self.examine_example(lts_in, reachable, reduced_expected, remove_internal_loops=remove_internal_loops)

    def test_minimal1(self):
        """
        Tests reduction of a minimal LTS.
        """

        lts = LTS(State(None))

        self.examine_multiple(lts, (reach_wbisim, True, lts), (reach_sbisim, False, lts), (reach_ocong, False, lts))

    def test_minimal2(self):
        """
        Tests reduction of a minimal LTS.
        """

        s0 = State(None)
        s0.add_transition(Transition(None, s0))
        lts1 = LTS(State(None))

        lts2 = LTS(State(None))

        self.examine_multiple(lts1, (reach_sbisim, False, lts1), (reach_ocong, False, lts1))

    def test_small1(self):
        """
        Tests reduction of a small LTS.
        """

        s0, s1, s2 = [State(None) for _ in range(3)]
        s0.add_transition(Transition(None, s1))
        s1.add_transition(Transition("a", s2))
        lts = LTS(s0)

        s0, s1 = [State(None) for _ in range(2)]
        s0.add_transition(Transition("a", s1))
        reduced = LTS(s0)

        self.examine_multiple(lts, (reach_wbisim, True, lts), (reach_sbisim, False, lts), (reach_ocong, False, lts))
