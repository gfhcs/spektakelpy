import abc

class Reference(abc.ABC):
    """
    A reference points to a part of a machine state.
    """

    def write(self, mstate, value):

    def read(self, mstate):
