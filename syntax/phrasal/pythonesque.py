from syntax.ast import Identifier, Constant, Tuple, Attribute, Projection, Call, BinaryOperation, \
    ArithmeticBinaryOperator, UnaryOperation, UnaryOperator, ArithmeticBinaryOperation, ComparisonOperator, Comparison, \
    BooleanBinaryOperation, BooleanBinaryOperator, AssignableExpression, Assignment, ExpressionStatement, Return, \
    Continue, Break, Block, Nop, While, Await, Launch
from syntax.lexer import keyword, identifier
from syntax.parser import Parser, ParserError
from syntax.lexical.pythonesque import TokenType

ID = TokenType.IDENTIFIER
LT = TokenType.LITERAL
KW = TokenType.KEYWORD
NL = TokenType.NEWLINE
INDENT = TokenType.INDENT
DEDENT = TokenType.DEDENT


def end(token):
    t, s, (o, l, c) = token
    o += len(s)

    if t == LT and s.startswith("\"\"\""):
        for line in s.iterlines():
            l += 1
        l -= 1
        c = len(line)
        return TokenPosition(o, l, c)
    elif t in (INDENT, DEDENT):
        return TokenPosition(o, l, c)
    else:
        return TokenPosition(o, l, c + len(s))


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
            return Identifier(s, start=p, end=end(lexer.read()))
        elif t == LT:
            return Constant(s, start=p, end=end(lexer.read()))
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
                        return Tuple(*components, start=p, end=end(lexer.read()))
                    else:
                        assert len(components) == 1
                        return components[0]

        raise ParserError("Expected an identifier, literal, or opening parenthesis!", p)

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
                name = lexer.match(identifier())
                e = Attribute(e, name[1], start=e.start, end=end(name))
            elif t == KW and s == "[":
                lexer.read()
                index = cls.parse_expression(lexer)
                e = Projection(e, index, start=e.start, end=end(lexer.match(keyword("]"))))
            elif t == KW and s == "(":
                lexer.read()
                args = []
                require_comma = False
                while True:
                    if lexer.seeing(keyword(")")):
                        ep = end(lexer.read())
                        break
                    if require_comma:
                        lexer.match(keyword(","))
                    args.append(cls.parse_expression(lexer))
                    require_comma = True

                e = Call(e, *args, start=e.start, end=ep)
            else:
                return e

            t, s, p = lexer.peek()

    @classmethod
    def _parse_call(cls, lexer):
        """
        Behaves like _parse_application, but makes sure that the resulting expression is of type Call.
        :param lexer: The lexer to consume tokens from.
        :return: An Expression node.
        """

        c = cls._parse_application(lexer)

        if not isinstance(c, Call):
            raise ParserError("Expected a call expression, but found a different kind of expression!", c.start)

        return c

    @classmethod
    def _parse_async(cls, lexer):
        """
        Parses either a 'process' expression or an 'await' expression, or behaves like _parse_application.
        :param lexer: The lexer to consume tokens from.
        :return: An Expression node.
        """
        t, s, p = lexer.peek()

        if t == KW and s == "await":
            lexer.read()
            e = cls._parse_application(lexer)
            return Await(e, start=p, end=e.end)
        elif t == KW and s == "process":
            lexer.read()
            e = cls._parse_call(lexer)
            return Launch(e, start=p, end=e.end)
        else:
            return cls._parse_application(lexer)


    @classmethod
    def _parse_pow(cls, lexer):
        """
        Parses either an exponentiation, or behaves like _parse_async.
        :param lexer: The lexer to consume tokens from.
        :return: An Expression node.
        """
        base = cls._parse_application(lexer)
        t, s, p = lexer.peek()

        while t == KW and s == "**":
            lexer.read()
            e = cls._parse_application(lexer)
            base = BinaryOperation(ArithmeticBinaryOperator.POWER, base, e, start=base.start, end=e.end)

        return base

    @classmethod
    def _parse_unary(cls, lexer):
        """
        Either parses a unary minus expression or behaves like _parse_pow.
        :param lexer: The lexer to consume tokens from.
        :return: An Expression node.
        """

        start = None
        positive = True
        while lexer.seeing(keyword("-")):
            _, _, p = lexer.read()
            if start is None:
                start = p
            positive = not positive

        e = cls._parse_pow(lexer)

        if positive:
            return e
        else:
            return UnaryOperation(UnaryOperator.MINUS, e, start=e.start if start is None else start, end=e.end)

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
            base = ArithmeticBinaryOperation(op, base, right, start=base.start, end=right.end)

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
            base = ArithmeticBinaryOperation(op, base, right, start=base.start, end=right.end)

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
            base = Comparison(op, base, right, start=base.start, end=right.end)

    @classmethod
    def _parse_not(cls, lexer):
        """
        Either parses a boolean NOT expression or behaves like _parse_comparison.
        :param lexer: The lexer to consume tokens from.
        :return: An Expression node.
        """

        start = None
        positive = True
        while lexer.seeing(keyword("not")):
            _, _, p = lexer.read()
            if start is None:
                start = p
            positive = not positive

        e = cls._parse_comparison(lexer)

        if positive:
            return e
        else:
            return UnaryOperation(UnaryOperator.NOT, e, start=e.start if start is None else start, end=e.end)

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
            base = BooleanBinaryOperation(BooleanBinaryOperator.AND, base, right, start=base.start, end=right.end)

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
            base = BooleanBinaryOperation(BooleanBinaryOperator.OR, base, right, start=base.start, end=right.end)

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
                e = Tuple(*es, start=es[0].start, end=lexer.peek()[-1])

            if t == KW and s == ":":
                if not isinstance(e, Identifier):
                    raise ParserError("Only an identifier is allowed on the left hand side of ':'!", pos=lexer.peek()[-1])
                lexer.read()
                s = cls._parse_statement(lexer)
                return ActionStatement(e, s, start=e.start, end=lexer.peek()[-1])
            elif t == KW and s == "=":
                if not isinstance(e, AssignableExpression):
                    raise ParserError("Only 'assignable' expressions must occuron the left hand side of an assignment!",
                                      pos=lexer.peek()[-1])
                lexer.read()
                right = cls.parse_expression(lexer)
                return Assignment(e, right, start=e.start, end=lexer.peek()[-1])
            else:
                return ExpressionStatement(e, start=e.start, end=lexer.peek()[-1])

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
        return Return(e, start=p, end=e.end)

    @classmethod
    def _parse_continue(cls, lexer):
        """
        Parses a continue statement.
        :param lexer: The lexer to consume tokens from.
        :return: A Continue node.
        """
        t = lexer.match(keyword("continue"))
        return Continue(start=t[-1], end=end(t))

    @classmethod
    def _parse_break(cls, lexer):
        """
        Parses a break statement.
        :param lexer: The lexer to consume tokens from.
        :return: A Break node.
        """
        t = lexer.match(keyword("break"))
        return Break(start=t[-1], end=end(t))

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
    def _parse_if(cls, lexer):
        """
        Parses an 'if' statement.
        :param lexer: The lexer to consume tokens from.
        :return: A Statement node.
        """
        _, _, start = lexer.match(keyword("if"))

        lexer.match(keyword("("))
        condition = cls.parse_expression(lexer)
        lexer.match(keyword(")"))
        consequence = cls._parse_statement(lexer)

        t, s, p = lexer.peek()
        if t == KW and s == "else":
            lexer.read()
            alternative = cls._parse_statement(lexer)
        else:
            alternative = Nop()

        return Select([
            When(condition, consequence, start=start, end=consequence.end),
            When(UnaryOperation(UnaryOperator.NOT, condition, start=alternative.start, end=alternative.start),
                 alternative, start=alternative.start, end=alternative.end)
        ], start=start, end=lexer.peek()[-1])

    @classmethod
    def _parse_while(cls, lexer):
        """
        Parses a 'while' statement.
        :param lexer: The lexer to consume tokens from.
        :return: A While node.
        """
        _, _, start = lexer.match(keyword("while"))

        lexer.match(keyword("("))
        condition = cls.parse_expression(lexer)
        lexer.match(keyword(")"))
        body = cls._parse_statement(lexer)

        return While(condition, body, start=start, end=lexer.peek()[-1])

    @classmethod
    def _parse_procdef(cls, lexer):
        # TODO: Implement procedure definition parsing
        pass

    def _parse_declaration(cls, lexer):

        # Like with statements, we have to branch into the different declaration types here.

    @classmethod
    def _parse_declarations(cls, lexer):
        # TODO: This should simply parse a sequence of declarations.

    def _parse_decl_label(cls, lexer):
        # TODO: Parses a label declaration (offer or sync)

    def _parse_decl_var(cls, lexer):
        # TODO: Parses a variable declaration

    def _parse_decl_procdure(cls, lexer):
        # TODO: Parses a procedure declaration (either def or public)

    def _parse_decl_property(cls, lexer):
        # TODO: Parses a property declaration.

    def _parse_decl_process(cls, lexer):
        # TODO: Parses a process declaration

    def _parse_decl_pheno(cls, lexer):
        # TODO: This should mostly call _parse_declarations.

    @classmethod
    def parse_behavior(cls, lexer):
        return cls._parse_pheno

     @classmethod
    def parse_block(cls, lexer):

         pass