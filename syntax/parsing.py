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
        t, s, p = lexer.peek()
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
    def _parse_statement(cls, lexer):
        """
        Parses a statement.
        :param lexer: The lexer to consume tokens from.
        :return: A Statement node.
        """
        t, s, p = lexer.peek()

        cs = {(KW, "{"): cls._parse_block,
              (KW, "return"): cls._parse_return,
              (KW, "break"): cls._parse_break,
              (KW, "continue"): cls._parse_continue,
              (KW, "when"): cls._parse_when,
              (KW, "select"): cls._parse_select,
              (KW, "if"): cls._parse_if,
              (KW, "while"): cls._parse_while,
              (KW, "def"): cls._parse_procdef}

        try:
            sub_parser = cs[(t, s)]
        except KeyError:
            es = [cls.parse_expression(lexer)]

            t, s, p = lexer.peek()

            while t == KW and s == ",":
                lexer.read()
                es.append(cls.parse_expression(lexer))
                t, s, p = lexer.peek()

            if len(es) == 1:
                e = es
            else:
                e = Tuple(*es, start=es[0].start, end=lexer.position)

            if t == KW and s == ":":
                if not isinstance(e, Identifier):
                    raise ParserError("Only an identifier is allowed on the left hand side of ':'!", pos=lexer.position)
                lexer.read()
                s = cls._parse_statement(lexer)
                return ActionStatement(e, s, start=e.start, end=lexer.position)
            elif t == KW and s == "=":
                if not isinstance(e, AssignableExpression):
                    raise ParserError("Only 'assignable' expressions must occuron the left hand side of an assignment!",
                                      pos=lexer.position)
                lexer.read()
                right = cls.parse_expression(lexer)
                return Assignment(e, right, start=e.start, end=lexer.position)
            else:
                return ExpressionStatement(e, start=e.start, end=lexer.position)

        return sub_parser(lexer)

    @classmethod
    def _parse_return(cls, lexer):
        """
        Parses a return statement.
        :param lexer: The lexer to consume tokens from.
        :return: A Return node.
        """
        _, _, p = lexer.match(keyword("return"))
        e = cls.parse_expression(lexer)
        return Return(e, start=p, end=lexer.position)

    @classmethod
    def _parse_continue(cls, lexer):
        """
        Parses a continue statement.
        :param lexer: The lexer to consume tokens from.
        :return: A Continue node.
        """
        _, _, p = lexer.match(keyword("continue"))
        return Continue(start=p, end=lexer.position)

    @classmethod
    def _parse_break(cls, lexer):
        """
        Parses a break statement.
        :param lexer: The lexer to consume tokens from.
        :return: A Break node.
        """
        _, _, p = lexer.match(keyword("break"))
        return Break(start=p, end=lexer.position)

    @classmethod
    def _parse_statements(cls, lexer, t):
        """
        Parses a sequence of statements.
        :param lexer: The lexer to consume tokens from.
        :param t: A predicate over tokens, deciding if the current token delimits the end of the statement list.
        :return: A list of Statement nodes.
        """
        ss = []
        while not t(lexer.peek()):
            ss.append(cls._parse_statement(lexer))

        return ss

    @classmethod
    def _parse_block(cls, lexer):
        """
        Parses a block statement.
        :param lexer: The lexer to consume tokens from.
        :return: A Block node.
        """
        _, _, start = lexer.match(keyword("{"))
        statements = cls._parse_statements(lexer, keyword("}"))
        lexer.match(keyword("}"))
        return Block(statements, start=start, end=lexer.position)

    @classmethod
    def _parse_when(cls, lexer):
        """
        Parses a 'when' statement.
        :param lexer: The lexer to consume tokens from.
        :return: A When node.
        """
        _, _, start = lexer.match(keyword("when"))

        lexer.match(keyword("("))
        condition = cls.parse_expression(lexer)
        lexer.match(keyword(")"))
        statement = cls._parse_statement(lexer)

        return When(condition, statement, start=start, end=lexer.position)

    @classmethod
    def _parse_select(cls, lexer):
        """
        Parses a 'select' statement.
        :param lexer: The lexer to consume tokens from.
        :return: A Select node.
        """
        _, _, start = lexer.match(keyword("select"))

        lexer.match(keyword("{"))

        t, s, p = lexer.peek()

        def t(token):
            t, s, p = token
            return t == KW and s in ("::", "}")

        alternatives = []
        while not (t == KW and s == "}"):
            _, _, sstart = lexer.match(keyword("::"))

            ss = cls._parse_statements(lexer, t)
            if len(ss) != 1:
                s = Block(ss, start=sstart, end=lexer.position)
            else:
                s, = ss

            alternatives.append(s)

        lexer.match(keyword("}"))

        return Select(alternatives, start=start, end=lexer.position)


    @classmethod
    def _parse_while(cls, lexer):
        pass

    @classmethod
    def _parse_procdef(cls, lexer):
        pass

    @classmethod
    def parse_process(cls, lexer):
        return cls._parse_statement
