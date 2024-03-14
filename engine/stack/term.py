import abc

from util import check_types
from util.immutable import Immutable
from util.printable import Printable


class Term(Immutable, Printable, abc.ABC):
    """
    A term is a type of expression that is evaluated atomically and functionally, meaning that intermediate states
    of its evaluation are not semantically observable and that evaluation cannot change the machine state ever.
    Even when evaluation should fail, an error is merely reported as an exception.

    Terms can be seen as a special type of machine instruction: Instead of making the instruction set of our virtual
    machine rather large, to support all the different ways in which computations can be combined, we keep the set of
    proper instructions quite small and use terms whenever possible. Terms are beneficial mostly because they do not
    change the machine state and thus can be evaluated safely without unforeseen side effects.
    """

    def __init__(self, *children):
        super().__init__()
        self._children = check_types(children, Term)

    def __ne(self, other):
        return not self.__eq__(other)

    @abc.abstractmethod
    def evaluate(self, tstate, mstate):
        """
        Evaluates this expression in the given state.
        :param tstate: The task state that this expression is to be evaluated in. It must be part of the given machine
        state. Any references to task-local variables will be interpreted with respect to this task state.
        :param mstate: The machine state that this expression is to be evaluated in. It must contain the given task
        state.
        :exception VException: If evaluation fails for a semantic reason.
        :return: An object representing the value that evaluation resulted in.
        """
        pass

    @property
    def children(self):
        """
        The children of this term.
        """
        return self._children
