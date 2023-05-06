import abc


class Type(Value):
    """
    A Type describes a set of abilities and an interface that a value provides.
    """

    def resolve_member(self, name, instance):
        """
        Retrieves the type member of the given name.
        :param name: The name of the member to retrieve.
        :param instance: The Value object for which to retrieve the member.
        :return: Either a Reference object, or a Procedure object.
        """
        pass

    def subtypeof(self, other):
        pass



# Built-in data types should be the same as for python: bool, int, float, str, tuple, list, dict, object, type, exception, task, function, module


class TException(Type):
    pass


TException.instance = TException()


class TFunction(Type):
    pass


TFunction.instance = TFunction()

class TClass(Type):
    pass