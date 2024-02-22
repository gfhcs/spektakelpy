import unittest

from state_space.equivalence import reduce, reach_wbisim, reach_sbisim, reach_ocong, reach_cached, isomorphic, bisimilar
from state_space.lts import State, LTS, Transition


class TestBisimilarity(unittest.TestCase):
    """
    This class contains test cases for our bisimilarity utility procedures.
    """

    def examine_example(self, lts_in, reachable, lts_reference, positive, remove_internal_loops):
        """
        Assesses the equivalence of two LTS's under a given bisimilarity definition.
        :param lts_in: The LTS to examine.
        :param reachable: The 'reachable' procedure to use, defining a type of bisimilarity.
        :param lts_reference: The LTS to which lts_in should be compared.
        :param positive: Whether we expect the LTS's to be equivalent (True), or not equivalent (False).
        :param remove_internal_loops: Specifies if reduction of LTSs should remove internal transitions leading from
                                      a state back into the same state.

        """

        lts_reduced = reduce(lts_in, reach_cached(reachable), remove_internal_loops=remove_internal_loops)

        b = bisimilar(reachable, lts_in, lts_reference)
        i = isomorphic(lts_reduced, lts_reference)

        if positive:
            self.assertTrue(b, msg="Bisimilarity was expected, but not found!")
            self.assertTrue(i, msg="Isomorphy was expected, but not found!")
        else:
            self.assertFalse(b, msg="Bisimilarity was not expected, but found!")
            self.assertFalse(i, msg="Isomorphy was not expected, but found!")

    def examine_multiple(self, lts_in, *r2e):
        """
        Reduces an LTS according to multiple bisimilarity definitions and compares results to expectations.
        :param lts_in: The LTS to reduce.
        :param r2e: An iterable of tuples (reachable, reference, positive), to be used for calling self.examine_example.
        """

        r2s = {id(reach_wbisim): ("weak", True),
               id(reach_sbisim): ("strong", False),
               id(reach_ocong): ("ocong", False)}

        for reachable, reference, positive in r2e:
            type, remove_internal_loops = r2s[id(reachable)]
            with self.subTest(msg=f"{type}: {'yes' if positive else 'no'}"):
                self.examine_example(lts_in, reachable, reference, positive, remove_internal_loops=remove_internal_loops)

    def test_minimal1(self):
        """
        Tests reduction of a minimal LTS.
        """

        lts = LTS(State(None).seal())

        self.examine_multiple(lts, (reach_wbisim, lts, True), (reach_sbisim, lts, True), (reach_ocong, lts, True))

    def test_minimal2(self):
        """
        Tests reduction of a minimal LTS.
        """

        s0 = State(None)
        s0.add_transition(Transition(None, s0))
        lts1 = LTS(s0.seal())

        lts2 = LTS(State(None).seal())

        self.examine_multiple(lts1, (reach_wbisim, lts2, True), (reach_sbisim, lts2, False), (reach_ocong, lts2, False))

    def test_small1(self):
        """
        Tests reduction of a small LTS.
        """

        s0, s1, s2 = [State(None) for _ in range(3)]
        s0.add_transition(Transition(None, s1))
        s1.add_transition(Transition("a", s2))
        lts = LTS(s0.seal())

        s0, s1 = [State(None) for _ in range(2)]
        s0.add_transition(Transition("a", s1))
        reduced = LTS(s0.seal())

        self.examine_multiple(lts,
                              (reach_wbisim, reduced, True),
                              (reach_sbisim, reduced, False),
                              (reach_ocong, reduced, False))
