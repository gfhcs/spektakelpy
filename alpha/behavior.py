

class Context:
    """
    An object that represents the context in which the behavior of a context is specified.
    """
    # TODO: Implement Context.
    pass


class LambdaBehavior:
    """
    Encapsulates a Python procedure that specifies (part of) the behavior of a process.
    """
    # TODO: Implement LambdaBehavior

    @staticmethod
    def concurrent(*lambdas):
        """
        Computes the interleaving semantics of a number of lambda behaviors.
        :param lambdas:
        :return: A LambdaBehavior.
        """
        # TODO: Implement LambdaBehavior.concurrent
        raise NotImplementedError()


class LambdaProcess:
    """
    A process the behavior of which is specified in the form of Python procedures.
    """
    # TODO: Implement LambdaProcess.
    pass