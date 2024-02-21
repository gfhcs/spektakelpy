import unittest

from state_space.equivalence import reduce, reach_wbisim, reach_sbisim, reach_ocong, reach_cached, isomorphic
from state_space.lts import State, LTS


class TestBisimilarity(unittest.TestCase):
    """
    This class contains test cases for our bisimilarity utility procedures.
    """

    def examine_example(self, lts_in, reachable, reduced_expected):
        """
        Reduces an LTS according to some bismilarity definition and compares the result to the expected one.
        :param lts_in: The LTS to reduce.
        :param reachable: The 'reachable' procedure to use, defining the type of bisimilarity according to which
                          the LTS is to be reduced.
        :param reduced_expected: The LTS that we expect the reduction result to be isomorphic to.
        """

        lts_out = reduce(lts_in, reach_cached(reachable))
        self.assertTrue(isomorphic(lts_out, reduced_expected))

    def examine_multiple(self, lts_in, *r2e):
        """
        Reduces an LTS according to multiple bisimilarity definitions and compares results to expectations.
        :param lts_in: The LTS to reduce.
        :param r2e: An iterable of pairs (reachable, reduced_expected), to be used for calling self.examine_example.
        """

        r2s = {id(reach_wbisim): "weak",
               id(reach_sbisim): "strong",
               id(reach_ocong): "ocong"}

        for reachable, reduced_expected in r2e:
            with self.subTest(type=r2s[id(reachable)]):
                self.examine_example(lts_in, reachable, reduced_expected)

    def test_minimal(self):
        """
        Tests reduction of the minimal LTS.
        """

        lts = LTS(State(None))

        self.examine_multiple(lts, (reach_wbisim, lts), (reach_sbisim, lts), (reach_ocong, lts))
