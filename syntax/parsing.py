import abc


class Parser(abc.ABC):
    """
    A parser turns sequences of tokens into abstract syntax trees.
    """

    @abc.abstractmethod
    def parse_expression(self, lexer):
        """
        Parses the AST of an expression.
        :param lexer: The lexer to consume tokens from.
        :return: An expression object.
        """
        pass

    @abc.abstractmethod
    def parse_process(self, lexer):
        """
        Parses the AST of a process.
        :param lexer: The lexer to consume tokens from.
        :return: A Statement object.
        """
        pass