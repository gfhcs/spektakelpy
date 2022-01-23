import abc


class Visual(abc.ABC):
    """
    An object with a visual representation.
    """

    @property
    @
    def origin(self):

    # TODO: This should have a position.

    @abc.abstractmethod
    def intersect(self, ray):
        """
        Decides in which way a ray intersects this visual.
        :param ray: A ray through the stage space.
        :returns: An Intersection object indicating the way in which the given ray intersects this visual.
        """
        pass
