import abc
from util.immutable import Sealable

class Reference(Sealable):
    """
    A reference points to a part of a machine state.
    """

    def write(self, mstate, value):

    def read(self, mstate):
