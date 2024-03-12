
class Singleton:
    """
    A type of which only one instance can exist.
    """

    def __new__(cls):
        try:
            return cls.instance
        except AttributeError:
            cls.__instance = super().__new__(cls)
            return cls.instance
