from core.visual import Visual


class Widget(Visual):
    """
    A 2-dimensional visual that is placed in the image plane.
    """

    def intersect(self, ray):
        """
        Decides in which way a ray intersects this visual.
        :param ray: A ray through the stage space.
        :returns: An Intersection object indicating the way in which the given ray intersects this visual.
        """
        pass

        # TODO: Call self.rasterize!

    @abc.abstractmethod
    def rasterize(self):


        pass