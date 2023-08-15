import unittest


class TestSpektakelTranslation(unittest.TestCase):
    """
    This class is for testing the translation from high-level Spektakel code into low-level VM code.
    """

    def test_empty(self):
        """
        Tests if the empty program is executed successfully.
        """
        # TODO: Combine the facilities from the validation test suite and the machine test suite in orer to test
        #       the execution of the empty program.
