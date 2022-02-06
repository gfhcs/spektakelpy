from util import check_type
from .expressions import Expression
from .instructions import Instruction


class Edge:
    """
    Represents a control flow edge.
    """

    def __init__(self, guard, instructions, destination):
        """
        Creates a new control flow edge.
        :param guard: An expression that indicates when this edge is enabled.
        :param instructions: The sequence of instructions that is to be executed when this edge is followed.
        :param destination: The control flow location that this edge leads into.
        """
        self._guard = check_type(guard, Expression)
        self._destination = check_type(destination, int)
        self._instructions = tuple(check_type(i, Instruction) for i in instructions)

    @property
    def guard(self):
        """
        An Expression that indicates when this edge is enabled.
        :return: An Expression object.
        """
        return self._guard

    @property
    def instructions(self):
        """
        The sequence of instructions that is to be executed when this edge is followed.
        """
        return self._instructions

    @property
    def destination(self):
        """
        The control flow location that this edge leads into.
        :return: An integer.
        """
        return self._destination


class CFG:
    """
    Models control flow graphs, which consist of locations connected by edges.
    """

    def __init__(self, edges):
        """
        Creates a new control flow graph.
        :param edges: A tuple of tuples of Edge objects. The i-th component of this tuple comprises all the edges
        originating from the i-th control location.
        """
        super().__init__()
        self._edges = tuple(tuple(check_type(e, Edge) for e in es) for es in edges)

    @property
    def edges(self):
        """
        A tuple of tuples of Edge objects. The i-th component of this tuple comprises all the edges originating
        from the i-th control location.
        """
        return self._edges
