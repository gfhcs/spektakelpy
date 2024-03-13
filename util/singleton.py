
class Singleton:
    """
    A type that has only one single instance. All constructor calls return that same instance.
    """

    instance = None

    def __new__(cls):
        if not isinstance(cls.instance, cls):
            cls.instance = super().__new__(cls)
        return cls.instance
