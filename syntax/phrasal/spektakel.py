from syntax.lexer import Lexer, expected
from syntax.lexical.pythonesque import TokenType, PythonesqueLexicalGrammar
from syntax.parser import Parser, ParserError
from syntax.phrasal.ast import *
from syntax.tokens import TokenPosition

ID = TokenType.IDENTIFIER
LT = TokenType.LITERAL
KW = TokenType.KEYWORD
NL = TokenType.NEWLINE
INDENT = TokenType.INDENT
DEDENT = TokenType.DEDENT


separators = ["+", "-", "*", "**", "/", "//", "%", "@", "<<", ">>", "&", "|", "^", "~", ":=", "<", ">", "<=", ">=",
              "==", "!=", "(", ")", "[", "]", "{", "}", ",", ":", ".", ";", "@", "=", "->", "+=", "-=", "*=", "/=",
              "//=", "%=", "@=", "&=", "|=", "^=", ">>=", "<<=", "**="]

keywords = ["False", "await", "else", "import", "pass", "None", "break", "except", "in", "raise", "True", "class",
            "finally", "is", "return", "and", "continue", "for", "lambda", "try", "as", "def", "from", "nonlocal",
            "while", "assert", "del", "global", "not", "with", "async", "elif", "if", "or", "yield",
            "var", "atomic", "prop", "get", "set"]

lexical_grammar = PythonesqueLexicalGrammar(separators=separators, keywords=keywords, chunk_size=1024)


class SpektakelLexer(Lexer):
    """
    A Lexer using the the lexical grammar for the Spektakel language.
    """
    def __init__(self, source):
        super().__init__(lexical_grammar, source)


def keyword(s=None):
    """
    Constructs a predicate asserting that a given token is the expected keyword.
    :param s: The expected text of the token.
    :return: A predicate procedure.
    """
    return expected(t=TokenType.KEYWORD, s=s)


def identifier(s=None):
    """
    Constructs a predicate asserting that a given token is an identifier.
    :param s: The expected text of the token.
    :return: A predicate procedure.
    """
    return expected(t=TokenType.IDENTIFIER, s=s)


def literal():
    """
    Constructs a predicate asserting that a given token is a literal.
    :return: A predicate procedure.
    """
    return expected(t=TokenType.LITERAL)


def end(token):
    """
    Given a token, returns the TokenPosition of the *end* of the token.
    :param token: A triple (t, s, p), as emitted by a lexer.
    :return: A TokenPosition object.
    """
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


def match_newline(lexer, enabled=True):
    """
    Consumes a newline token from the given lexer.
    :param lexer: The lexer to consume the token from.
    :param enabled: Whether this call should actually have an effect (True, default), or not (False).
    """
    if enabled:
        def newline(token):
            return token[0] == NL

        lexer.match(newline)


def match_indent(lexer):
    """
    Consumes an INDENT token from the given lexer.
    :param lexer: The lexer to consume the token from.
    """
    lexer.match(lambda token: token[0] == INDENT)


def match_dedent(lexer):
    """
    Consumes an DEDENT token from the given lexer.
    :param lexer: The lexer to consume the token from.
    """
    lexer.match(lambda token: token[0] == DEDENT)


class SpektakelParser(Parser):
    """
    A parser for the spektakelpy default language.
    """

    @classmethod
    def _parse_identifier(cls, lexer):
        """
        Parses exactly one identifier.
        :param lexer: The lexer to consume tokens from.
        :return: An Expression node.
        """
        t, s, p = lexer.match(identifier())
        return Identifier(s, start=p, end=end((t, s, p)))

    @classmethod
    def _parse_simple_expression(cls, lexer):
        """
        Parses a "simple expression", i.e. either an identifier, a literal, a parenthesized expression,
        or a tuple expression.
        :param lexer: The lexer to consume tokens from.
        :return: An Expression node.
        """
        t, s, start = lexer.peek()

        if t == ID:
            return Identifier(s, start=start, end=end(lexer.read()))
        elif t == LT:
            return Constant(s, start=start, end=end(lexer.read()))
        elif t == KW and s == "(":
            lexer.read()
            components = []
            is_tuple = False
            while True:
                components.append(cls.parse_expression(lexer))
                if lexer.seeing(keyword(",")):
                    is_tuple = True
                    lexer.read()
                else:
                    t, s, p = lexer.match(keyword(")"))
                    if is_tuple:
                        return Tuple(*components, start=p, end=p)
                    else:
                        assert len(components) == 1
                        return components[0]

        raise ParserError("Expected an identifier, literal, or opening parenthesis!", start)

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
                name = cls._parse_identifier(lexer)
                e = Attribute(e, name, start=e.start, end=name.end)
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
            e = cls.parse_expression(lexer)
            return Await(e, start=p, end=e.end)
        elif t == KW and s == "async":
            lexer.read()
            e = cls.parse_expression(lexer)
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
        base = cls._parse_async(lexer)
        t, s, p = lexer.peek()

        while t == KW and s == "**":
            lexer.read()
            e = cls._parse_async(lexer)
            base = ArithmeticBinaryOperation(ArithmeticBinaryOperator.POWER, base, e, start=base.start, end=e.end)
            t, s, p = lexer.peek()

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

        # This method and the ones it calls respect are based on the parsing rules laid out in
        # https://docs.python.org/3/reference/compound_stmts.html

        t, s, start = lexer.peek()

        cs = {"pass": cls._parse_pass,
              "return": cls._parse_return,
              "break": cls._parse_break,
              "continue": cls._parse_continue,
              "if": cls._parse_if,
              "while": cls._parse_while,
              "def": cls._parse_def,
              "prop": cls._parse_prop,
              "class": cls._parse_class}

        if t == KW and s in cs:
            return (cs[s])(lexer)
        else:

            eparse = cls.parse_expression

            # Maybe this is a declaration?
            var = False
            if lexer.seeing(keyword("var")):
                lexer.read()
                var = True
                # For declarations, only (a tuple of) identifiers must be parsed.
                eparse = cls._parse_identifier

            # Parse an expression, which might be an unparenthesised tuple:
            es = [eparse(lexer)]
            t, s, p = lexer.peek()
            while t == KW and s == ",":
                lexer.read()
                es.append(eparse(lexer))
                t, s, p = lexer.peek()
            if len(es) == 1:
                e = es[0]
            else:
                e = Tuple(*es, start=es[0].start, end=es[-1].end)

            if t == KW and s == "=":
                if not isinstance(e, AssignableExpression):
                    raise ParserError("Only 'assignable' expressions must occur on the left hand side of '='!",pos=p)
                lexer.read()

                # Parse right hand side, which might be an unparenthesised tuple as well:
                rs = [cls.parse_expression(lexer)]
                t, s, p = lexer.peek()
                while t == KW and s == ",":
                    lexer.read()
                    rs.append(cls.parse_expression(lexer))
                    t, s, p = lexer.peek()
                if len(rs) == 1:
                    right = rs
                else:
                    right = Tuple(*rs, start=rs[0].start, end=rs[-1].end)

                match_newline(lexer)

                if var:
                    return VariableDeclaration(pattern=e, expression=right, start=start, end=right.end)
                else:
                    return Assignment(e, right, start=start, end=right.end)
            else:
                match_newline(lexer)
                if var:
                    return VariableDeclaration(pattern=e, expression=None, start=start, end=e.end)
                else:
                    return ExpressionStatement(e, start=e.start, end=e.end)

    @classmethod
    def _parse_return(cls, lexer, newline=True):
        """
        Parses a return statement.
        :param lexer: The lexer to consume tokens from.
        :param newline: Whether this statement parser should also match a newline token after the actual statement.
        :return: A Return node.
        """
        _, _, p = lexer.match(keyword("return"))
        e = cls.parse_expression(lexer)
        match_newline(lexer, enabled=newline)
        return Return(e, start=p, end=e.end)

    @classmethod
    def _parse_continue(cls, lexer, newline=True):
        """
        Parses a continue statement.
        :param lexer: The lexer to consume tokens from.
        :param newline: Whether this statement parser should also match a newline token after the actual statement.
        :return: A Continue node.
        """
        t = lexer.match(keyword("continue"))
        match_newline(lexer, enabled=newline)
        return Continue(start=t[-1], end=end(t))

    @classmethod
    def _parse_break(cls, lexer, newline=True):
        """
        Parses a break statement.
        :param lexer: The lexer to consume tokens from.
        :param newline: Whether this statement parser should also match a newline token after the actual statement.
        :return: A Break node.
        """
        t = lexer.match(keyword("break"))
        match_newline(lexer, enabled=newline)
        return Break(start=t[-1], end=end(t))

    @classmethod
    def _parse_pass(cls, lexer, newline=True):
        """
        Parses a pass statement.
        :param lexer: The lexer to consume tokens from.
        :param newline: Whether this statement parser should also match a newline token after the actual statement.
        :return: A Pass node.
        """
        t = lexer.match(keyword("pass"))
        match_newline(lexer, enabled=newline)
        return Pass(start=t[-1], end=end(t))

    @classmethod
    def _parse_body(cls, lexer):
        """
        Parses a sequence of statements, preceded by an INDENT token and followed by a DEDENT token.
        :param lexer: The lexer to consume tokens from.
        :return: A statement object.
        """

        match_indent(lexer)
        ss = []
        while not lexer.seeing(lambda token: token[0] == DEDENT):
            ss.append(cls._parse_statement(lexer))
        match_dedent(lexer)

        return Block(ss, start=ss[0].start, end=ss[-1].end)

    @classmethod
    def _parse_atomic(cls, lexer):
        """
        Parses an atomic block, i.e. a sequence of statements the execution of which is not to be interrupted by
        other processes.
        :param lexer: The lexer to consume tokens from.
        :return: An AtomicBlock node.
        """
        lexer.match(keyword("atomic"))
        lexer.match(keyword(":"))
        match_newline(lexer)
        return AtomicBlock(cls._parse_body(lexer))

    @classmethod
    def _parse_if(cls, lexer):
        """
        Parses an 'if' statement.
        :param lexer: The lexer to consume tokens from.
        :return: A Statement node.
        """

        def _recur(lexer):
            condition = cls.parse_expression(lexer)
            lexer.match(keyword(":"))
            match_newline(lexer)
            consequence = cls._parse_body(lexer)
            alternative = _parse_clause(lexer, False)
            end = consequence.end if alternative is None else alternative.end
            return Conditional(condition, consequence, alternative, start=start, end=end)

        def _parse_clause(lexer, initial=True):

            t, s, start = lexer.peek()

            if t != KW:
                raise ParserError("Expected a keyword!", start)

            if initial:
                lexer.match(keyword("if"))
                return _recur(lexer)
            elif not initial and s == "elif":
                lexer.read()
                return _recur(lexer)
            elif not initial and s == "else":
                lexer.read()
                lexer.match(keyword(":"))
                match_newline(lexer)
                alternative = cls._parse_body(lexer)
                return alternative
            else:
                return None

        return _parse_clause(lexer, True)

    @classmethod
    def _parse_while(cls, lexer):
        """
        Parses a 'while' statement.
        :param lexer: The lexer to consume tokens from.
        :return: A While node.
        """
        _, _, start = lexer.match(keyword("while"))
        condition = cls.parse_expression(lexer)
        lexer.match(keyword(":"))
        match_newline(lexer)
        body = cls._parse_body(lexer)
        return While(condition, body, start=start, end=body.end)

    @classmethod
    def _parse_prop(cls, lexer):
        """
        Parses a property declaration.
        :param lexer: The lexer to consume tokens from.
        :return: A PropertyDefinition node.
        """
        _, _, start = lexer.match(keyword("prop"))
        name = cls._parse_identifier(lexer)
        lexer.match(keyword(":"))
        match_newline(lexer)
        match_indent(lexer)
        lexer.match(keyword("get"))
        lexer.match(keyword(":"))
        match_newline(lexer)
        getter = cls._parse_body(lexer)
        if lexer.seeing(keyword("set")):
            lexer.match(keyword("set"))
            lexer.match(keyword(":"))
            match_newline(lexer)
            setter = cls._parse_body(lexer)
        else:
            setter = None
        match_dedent(lexer)
        end = getter.end if setter is None else setter.end
        return PropertyDefinition(name, getter, setter, start=start, end=end)

    @classmethod
    def _parse_def(cls, lexer):
        """
        Parses a procedure declaration.
        :param lexer: The lexer to consume tokens from.
        :return: A ProcedureDefintion node.
        """
        _, _, start = lexer.match(keyword("def"))
        name = cls._parse_identifier(lexer)
        lexer.match(keyword("("))
        argnames = []
        if not lexer.seeing(keyword(")")):
            argnames.append(cls._parse_identifier(lexer))
        while lexer.seeing(keyword(",")):
            lexer.read()
            argnames.append(cls._parse_identifier(lexer))
        lexer.match(keyword(")"))
        lexer.match(keyword(":"))
        match_newline(lexer)
        body = cls._parse_body(lexer)
        return ProcedureDefinition(name, argnames, body, start=start, end=body.end)

    def _parse_class(cls, lexer):
        """
        Parses a class declaration.
        :param lexer: The lexer to consume tokens from.
        :return: A ClassDefinition node.
        """
        _, _, start = lexer.match(keyword("class"))
        name = cls._parse_identifier(lexer)
        lexer.match(keyword("("))
        basenames = []
        if not lexer.seeing(keyword(")")):
            basenames.append(cls._parse_identifier(lexer))
        while lexer.seeing(keyword(",")):
            lexer.read()
            basenames.append(cls._parse_identifier(lexer))
        lexer.match(keyword(")"))
        lexer.match(keyword(":"))
        match_newline(lexer)
        body = cls._parse_body(lexer)
        return ClassDefinition(name, basenames, body, start=start, end=body.end)

    @classmethod
    def parse_block(cls, lexer):
        """
        Parses a sequence of statements, followed by the end of the input stream.
        :param lexer: The lexer to consume tokens from.
        :return: A Statement object.
        """
        start = None
        end = None
        ss = []
        while not lexer.seeing(lambda token: token[0] == TokenType.END):
            ss.append(cls._parse_statement(lexer))

        if not lexer.seeing(lambda token: token[0] == TokenType.END):
            raise ParserError("Expected end of input!", lexer.peek()[-1])

        if len(ss) > 0:
            start = ss[0].start
            end = ss[-1].end
        else:
            _, _, start = lexer.peek()
            end = start

        return Block(ss, start=start, end=end)
