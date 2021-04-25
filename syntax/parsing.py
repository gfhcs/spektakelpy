import abc
from .ast import *


class Parser(abc.ABC):
    """
    A parser turns sequences of tokens into abstract syntax trees.
    """

    @staticmethod
    @abc.abstractmethod
    def parse_expression(self, lexer):
        """
        Parses the AST of an expression.
        :param lexer: The lexer to consume tokens from.
        :return: An expression object.
        """
        pass

    @staticmethod
    @abc.abstractmethod
    def parse_process(self, lexer):
        """
        Parses the AST of a process.
        :param lexer: The lexer to consume tokens from.
        :return: A Statement object.
        """
        pass


class SpektakelLangParser(Parser):
    """
    A parser for the spektakelpy default language.
    """

    @staticmethod
    def _parse_simple_expression(lexer):
        # Either constant, or name, or parenthesized, or tuple, or call.
        pass

    @staticmethod
    def _parse_attribute(lexer):
        # Attribute
        pass

    @staticmethod
    def _parse_pow(lexer):

    @staticmethod
    def _parse_projection(lexer):
        # Projection or simple
        pass

    @staticmethod
    def _parse_unary(lexer):
        # only unary minus!
        pass

    @staticmethod
    def _parse_mult(lexer):
        # multiplication, division, modulo.
        pass

    @staticmethod
    def _parse_add(lexer):
        # addition, subtraction
        pass

    @staticmethod
    def _parse_comparison(lexer):
        # Comparison
        pass

    @staticmethod
    def _parse_not(lexer):
        # boolean not.
        pass

    @staticmethod
    def _parse_and(lexer):
        # boolean and.
        pass

    @staticmethod
    def _parse_or(lexer):
        # boolean and.
        pass


    @staticmethod
    def parse_expression(lexer):
        pass

    @staticmethod
    def _parse_expression_statement(lexer):
        pass

    @staticmethod
    def _parse_jump(lexer):
        # return, break or continue.
        pass

    @staticmethod
    def _parse_assignment(lexer):
        pass

    @staticmethod
    def _parse_update(lexer):
        pass

    @staticmethod
    def _parse_block(lexer):
        pass

    @staticmethod
    def _parse_action_statement(lexer):
        pass

    @staticmethod
    def _parse_when(lexer):
        pass

    @staticmethod
    def _parse_select(lexer):
        pass

    @staticmethod
    def _parse_while(lexer):
        pass

    @staticmethod
    def _parse_procdef(lexer):
        pass

    @staticmethod
    def parse_process(self, lexer):
        pass