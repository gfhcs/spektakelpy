import abc
from .ast import *
from .lexer import TokenType, keyword, identifier
from .types import String, Float, Int

ID = TokenType.IDENTIFIER
KW = TokenType.KEYWORD
LT = TokenType.LITERAL


class ParserError(Exception):
    """
    A failure to parse a token stream.
    """

    def __init__(self, msg, pos=None):
        """
        Instantiates a new LexError.
        :param msg: The message for this error.
        :param pos: The position in the input stream at which this error was encountered.
        """

        if pos is not None:
            msg = "Line {}, column {}: ".format(pos.line, pos.column) + msg

        super().__init__(msg)
        self._pos = pos

    @property
    def position(self):
        """
        The position in the lexer input stream at which this error occurred.
        :return: A TokenPosition object.
        """
        return self._pos


class Parser(abc.ABC):
    """
    A parser turns sequences of tokens into abstract syntax trees.
    """

    @classmethod
    @abc.abstractmethod
    def parse_expression(cls, lexer):
        """
        Parses the AST of an expression.
        :param lexer: The lexer to consume tokens from.
        :return: An expression object.
        """
        pass

    @classmethod
    @abc.abstractmethod
    def parse_process(cls, lexer):
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

    @classmethod
    def _parse_simple_expression(cls, lexer):
        """
        Parses a "simple expression", i.e. either an identifier, a literal, a parenthesized expression,
        or a tuple expression.
        :param lexer: The lexer to consume tokens from.
        :return: An Expression node.
        """
        t, s, p = lexer.peek()[0]
        if t == ID:
            lexer.read()
            return Identifier(s, start=p, end=lexer.position)
        elif t == LT:
            lexer.read()
            if s.startswith("\""):
                value = String(s[1:-1])
            else:
                try:
                    value = Int(s)
                except TypeError:
                    value = Float(s)
            return Constant(value, start=p, end=lexer.position)
        elif t == KW and s == "(":
            lexer.read()
            components = []
            is_tuple = False
            while True:
                components.append(cls.parse_expression(lexer))
                if lexer.seeing(keyword(",")):
                    is_tuple = True
                    lexer.read()
                if lexer.seeing(keyword(")")):
                    if is_tuple:
                        lexer.read()
                        return Tuple(*components, start=p, end=lexer.position)
                    else:
                        assert len(components) == 1
                        return components[0]

        raise ParserError("Expected an expression!", lexer.position)

    @classmethod
    def _parse_application(cls, lexer):
        """
        Parses either an attribute retrieval, a projection, or a call, or a "simple" expression.
        :param lexer: The lexer to consume tokens from.
        :return: An Expression node.
        """
        e = cls._parse_simple_expression(lexer)
        t, s, p = lexer.peek()

        while True:
            if t == KW and s == ".":
                lexer.read()
                _, name, _ = lexer.match(identifier())
                e = Attribute(e, name, start=e.start, end=lexer.position)
            elif t == KW and s == "[":
                lexer.read()
                index = cls.parse_expression(lexer)
                lexer.match(keyword("]"))
                e = Projection(e, index, start=e.start, end=lexer.position)
            elif t == KW and s == "(":
                lexer.read()
                args = []
                require_comma = False
                while True:
                    if lexer.seeing(keyword(")")):
                        lexer.read()
                        break
                    if require_comma:
                        lexer.match(keyword(","))
                    args.append(cls.parse_expression(lexer))
                    require_comma = True

                e = Call(e, *args, start=e.start, end=lexer.position)
            else:
                return e

            t, s, p = lexer.peek()

    @classmethod
    def _parse_pow(cls, lexer):
        """
        Parses either an exponentiation, or behaves like _parse_application.
        :param lexer: The lexer to consume tokens from.
        :return: An Expression node.
        """
        base = cls._parse_application(lexer)
        t, s, p = lexer.peek()

        while t == KW and s == "**":
            lexer.read()
            e = cls._parse_application(lexer)
            base = BinaryOperation(ArithmeticBinaryOperator.POWER, base, e, start=base.start, end=lexer.position)

        return base

    @classmethod
    def _parse_unary(cls, lexer):
        """
        Either parses a unary minus expression or behaves like _parse_pow.
        :param lexer: The lexer to consume tokens from.
        :return: An Expression node.
        """

        positive = True
        while lexer.seeing(keyword("-")):
            lexer.read()
            positive = not positive

        e = cls._parse_pow(lexer)

        if positive:
            return e
        else:
            return UnaryOperation(UnaryOperator.MINUS, e, start=e.start, end=lexer.position)

    @classmethod
    def _parse_mult(cls, lexer):
        # multiplication, division, modulo.
        pass

    @classmethod
    def _parse_add(cls, lexer):
        # addition, subtraction
        pass

    @classmethod
    def _parse_comparison(cls, lexer):
        # Comparison
        pass

    @classmethod
    def _parse_not(cls, lexer):
        # boolean not.
        pass

    @classmethod
    def _parse_and(cls, lexer):
        # boolean and.
        pass

    @classmethod
    def _parse_or(cls, lexer):
        # boolean or.
        pass

    @classmethod
    def parse_expression(cls, lexer):
        return cls._parse_or(lexer)

    @classmethod
    def _parse_expression_statement(cls, lexer):
        e = cls.parse_expression(lexer)
        if lexer.seeing(keyword(",")):
            return e
        else:
            lexer.match(keyword(";"))
            return ExpressionStatement(e, start=e.start, end=lexer.position)

    @classmethod
    def _parse_jump(cls, lexer):
        # return, break or continue.
        pass

    @classmethod
    def _parse_assignment(cls, lexer):
        pass

    @classmethod
    def _parse_update(cls, lexer):
        pass

    @classmethod
    def _parse_block(cls, lexer):
        pass

    @classmethod
    def _parse_action_statement(cls, lexer):
        pass

    @classmethod
    def _parse_when(cls, lexer):
        pass

    @classmethod
    def _parse_select(cls, lexer):
        pass

    @classmethod
    def _parse_while(cls, lexer):
        pass

    @classmethod
    def _parse_procdef(cls, lexer):
        pass

    @classmethod
    def parse_process(cls, lexer):
        pass