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

    def test_small2(self):
        """
        Tests reduction of a small LTS.
        """

        s0, s1, s2, s3 = [State(None) for _ in range(4)]
        s0.add_transition(Transition("a", s1))
        s0.add_transition(Transition("a", s2))
        s1.add_transition(Transition("b", s3))
        s2.add_transition(Transition("c", s3))
        lts1 = LTS(s0.seal())

        s0, s1, s2 = [State(None) for _ in range(3)]
        s0.add_transition(Transition("a", s1))
        s1.add_transition(Transition("b", s2))
        s1.add_transition(Transition("c", s2))
        lts2 = LTS(s0.seal())

        self.examine_multiple(lts1,
                              (reach_wbisim, lts2, False),
                              (reach_sbisim, lts2, False),
                              (reach_ocong, lts2, False))

    def test_small3(self):
        """
        Tests reduction of a small LTS.
        """

        s0, s1, s2 = [State(None) for _ in range(3)]
        s0.add_transition(Transition("a", s1))
        s0.add_transition(Transition("b", s2))
        lts1 = LTS(s0.seal())

        s0, s1 = [State(None) for _ in range(2)]
        s0.add_transition(Transition("a", s1))
        s0.add_transition(Transition("b", s1))
        lts2 = LTS(s0.seal())

        self.examine_multiple(lts1,
                              (reach_wbisim, lts2, True),
                              (reach_sbisim, lts2, True),
                              (reach_ocong, lts2, True))

    def test_small4(self):
        """
        Tests reduction of a small LTS.
        """

        s0, s1 = [State(None) for _ in range(2)]
        s0.add_transition(Transition("a", s0))
        s0.add_transition(Transition("a", s1))
        lts1 = LTS(s0.seal())

        s0, = [State(None) for _ in range(1)]
        s0.add_transition(Transition("a", s0))
        lts2 = LTS(s0.seal())

        self.examine_multiple(lts1,
                              (reach_wbisim, lts2, False),
                              (reach_sbisim, lts2, False),
                              (reach_ocong, lts2, False))

    def test_small5(self):
        """
        Tests reduction of a small LTS.
        """

        s0, s1 = [State(None) for _ in range(2)]
        s0.add_transition(Transition(None, s1))
        s1.add_transition(Transition("a", s0))
        lts1 = LTS(s0.seal())

        s0, = [State(None) for _ in range(1)]
        s0.add_transition(Transition("a", s0))
        s0.add_transition(Transition(None, s0))
        lts2 = LTS(s0.seal())

        s0, = [State(None) for _ in range(1)]
        s0.add_transition(Transition("a", s0))
        lts3 = LTS(s0.seal())

        s0, s1 = [State(None) for _ in range(2)]
        s0.add_transition(Transition(None, s1))
        s1.add_transition(Transition("a", s0))
        s1.add_transition(Transition(None, s0))
        lts4 = LTS(s0.seal())

        self.examine_multiple(lts1,
                              (reach_wbisim, lts3, True),
                              (reach_sbisim, lts2, False),
                              (reach_ocong, lts2, False)
                              )

        self.examine_multiple(lts4, (reach_ocong, lts2, True))

    def test_small6(self):
        """
        Tests reduction of a small LTS.
        """

        s0, s1, s2 = [State(None) for _ in range(3)]
        s0.add_transition(Transition(None, s1))
        s0.add_transition(Transition("b", s2))
        s1.add_transition(Transition("a", s2))
        lts1 = LTS(s0.seal())

        s0, s1 = [State(None) for _ in range(2)]
        s0.add_transition(Transition("a", s1))
        s0.add_transition(Transition("b", s1))
        lts2 = LTS(s0.seal())

        s0, s1 = [State(None) for _ in range(2)]
        s0.add_transition(Transition("a", s1))
        s0.add_transition(Transition("b", s1))
        s0.add_transition(Transition(None, s0))
        lts3 = LTS(s0.seal())

        self.examine_multiple(lts1,
                              (reach_wbisim, lts2, False),
                              (reach_sbisim, lts2, False),
                              (reach_ocong, lts2, False),
                              (reach_ocong, lts3, False)
                              )

    def test_isomorphy(self):
        """
        Tests reduction of a small LTS. This test case is made for emphasizing on the correctness of isomorphy:
        The isomorphy bijection is one of many possible bijections between state spaces.
        """

        s0, s1, s2, s3, s4, s5 = [State(None) for _ in range(6)]
        s0.add_transition(Transition(None, s1))
        s0.add_transition(Transition(None, s2))
        s1.add_transition(Transition(None, s3))
        s2.add_transition(Transition(None, s4))
        s3.add_transition(Transition(None, s5))
        s4.add_transition(Transition(None, s5))
        lts1 = LTS(s0.seal())

        s0, s1, s2, s3, s4, s5 = [State(None) for _ in range(6)]
        s0.add_transition(Transition(None, s1))
        s0.add_transition(Transition(None, s2))
        s1.add_transition(Transition(None, s4))
        s2.add_transition(Transition(None, s3))
        s3.add_transition(Transition(None, s5))
        s4.add_transition(Transition(None, s5))
        lts2 = LTS(s0.seal())

        self.examine_multiple(lts1,
                              (reach_wbisim, reduce(lts1, reach_wbisim, remove_internal_loops=True), True),
                              (reach_sbisim, reduce(lts1, reach_sbisim), True),
                              (reach_ocong, reduce(lts1, reach_ocong), True),
                              (reach_wbisim, reduce(lts2, reach_wbisim, remove_internal_loops=True), True),
                              (reach_sbisim, reduce(lts2, reach_sbisim), True),
                              (reach_ocong, reduce(lts2, reach_ocong), True),
                              )

        with self.subTest(msg="isomorphy"):
            self.assertTrue(isomorphic(lts1, lts1))
            self.assertTrue(isomorphic(lts1, lts2))
            self.assertTrue(isomorphic(lts2, lts1))
            self.assertTrue(isomorphic(lts2, lts2))

    def test_tau_maze(self):
        """
        Tests the reduction of a large made of tau transitions.
        """

        def connect(sa, sb):
            sa.add_transition(Transition(None, sb))

        s0, s1, s2, s3, s4, s5, s6, s7, s8, s9 = [State(None) for _ in range(10)]
        s6.add_transition(Transition("a", s3))
        connect(s0, s1)
        connect(s1, s2)
        connect(s1, s3)
        connect(s1, s4)
        connect(s4, s2)
        connect(s5, s5)
        connect(s4, s1)
        connect(s3, s6)
        connect(s5, s3)
        connect(s9, s8)
        connect(s2, s8)
        connect(s8, s9)
        connect(s7, s8)
        connect(s7, s2)
        connect(s7, s5)
        connect(s1, s7)
        connect(s4, s5)
        connect(s9, s7)
        connect(s6, s6)

        lts1 = LTS(s0.seal())

        s0, = [State(None) for _ in range(1)]
        s0.add_transition(Transition("a", s0))
        lts2 = LTS(s0.seal())

        s0, = [State(None) for _ in range(1)]
        s0.add_transition(Transition("a", s0))
        s0.add_transition(Transition(None, s0))
        lts3 = LTS(s0.seal())

        self.examine_multiple(lts1,
                              (reach_wbisim, lts2, True),
                              (reach_sbisim, lts2, False),
                              (reach_ocong, lts2, False),
                              (reach_ocong, lts3, True)
                              )
