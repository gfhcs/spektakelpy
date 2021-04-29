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
        """
        Either parses a multiplicative expression (*, /, //, %) or behaves like _parse_unary.
        :param lexer: The lexer to consume tokens from.
        :return: An Expression node.
        """
        base = cls._parse_unary(lexer)

        t, s, p = lexer.peek()

        cs = {(KW, "*"): ArithmeticBinaryOperator.TIMES,
              (KW, "/"): ArithmeticBinaryOperator.OVER,
              (KW, "//"): ArithmeticBinaryOperator.INTOVER,
              (KW, "%"): ArithmeticBinaryOperator.MODULO}

        while True:
            try:
                op = cs[(t, s)]
            except KeyError:
                return base
            lexer.read()
            right = cls._parse_unary(lexer)
            base = ArithmeticBinaryOperation(op, base, right, start=base.start, end=lexer.position)

    @classmethod
    def _parse_add(cls, lexer):
        """
        Either parses a sum expression (+, -) or behaves like _parse_mult.
        :param lexer: The lexer to consume tokens from.
        :return: An Expression node.
        """
        base = cls._parse_mult(lexer)

        t, s, p = lexer.peek()

        cs = {(KW, "+"): ArithmeticBinaryOperator.PLUS,
              (KW, "-"): ArithmeticBinaryOperator.MINUS}

        while True:
            try:
                op = cs[(t, s)]
            except KeyError:
                return base
            lexer.read()
            right = cls._parse_mult(lexer)
            base = ArithmeticBinaryOperation(op, base, right, start=base.start, end=lexer.position)

    @classmethod
    def _parse_comparison(cls, lexer):
        """
        Either parses a comparison expression or behaves like _parse_add.
        :param lexer: The lexer to consume tokens from.
        :return: An Expression node.
        """
        base = cls._parse_add(lexer)

        t, s, p = lexer.peek()

        cs = {(KW, "in"): ComparisonOperator.IN,
              (KW, ">"): ComparisonOperator.GREATER,
              (KW, "=="): ComparisonOperator.EQ,
              (KW, ">="): ComparisonOperator.GREATEROREQUAL,
              (KW, "<"): ComparisonOperator.LESS,
              (KW, "<="): ComparisonOperator.LESSOREQUAL,
              (KW, "!="): ComparisonOperator.NEQ}

        while True:
            try:
                op = cs[(t, s)]
                lexer.read()
            except KeyError:
                if t == KW and s == "not":
                    lexer.read()
                    lexer.match(keyword("in"))
                    op = ComparisonOperator.NOTIN
                else:
                    return base
            right = cls._parse_add(lexer)
            base = Comparison(op, base, right, start=base.start, end=lexer.position)

    @classmethod
    def _parse_not(cls, lexer):
        """
        Either parses a boolean NOT expression or behaves like _parse_comparison.
        :param lexer: The lexer to consume tokens from.
        :return: An Expression node.
        """

        positive = True
        while lexer.seeing(keyword("not")):
            lexer.read()
            positive = not positive

        e = cls._parse_comparison(lexer)

        if positive:
            return e
        else:
            return UnaryOperation(UnaryOperator.NOT, e, start=e.start, end=lexer.position)

    @classmethod
    def _parse_and(cls, lexer):
        """
        Either parses a boolean AND expression or behaves like _parse_not.
        :param lexer: The lexer to consume tokens from.
        :return: An Expression node.
        """
        base = cls._parse_not(lexer)

        t, s, p = lexer.peek()

        while t == KW and s == "and":
            lexer.read()
            right = cls._parse_not(lexer)
            base = BooleanBinaryOperation(BooleanBinaryOperator.AND, base, right, start=base.start, end=lexer.position)

        return base

    @classmethod
    def _parse_or(cls, lexer):
        """
        Either parses a boolean OR expression or behaves like _parse_and.
        :param lexer: The lexer to consume tokens from.
        :return: An Expression node.
        """
        base = cls._parse_and(lexer)

        t, s, p = lexer.peek()

        while t == KW and s == "or":
            lexer.read()
            right = cls._parse_and(lexer)
            base = BooleanBinaryOperation(BooleanBinaryOperator.OR, base, right, start=base.start, end=lexer.position)

        return base

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