import abc
import io


class Printable(abc.ABC):
    """
    An object that can be efficiently formatted as a string.
    """

    @abc.abstractmethod
    def print(self, out):
        """
        Writes a human-readable string to the given file-like object that denotes this term.
        :param out: An io.TextIOBase to which the string representation of this term should be written.
        """
        pass

    def __str__(self):
        with io.StringIO() as s:
            self.print(s)
            return s.getvalue()

