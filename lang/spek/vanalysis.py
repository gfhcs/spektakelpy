from itertools import chain

from lang.spek.ast import Identifier, Pass, ExpressionStatement, Assignment, Return, Raise, Continue, Break, Block, \
    VariableDeclaration, Conditional, While, For, Try, ProcedureDefinition, PropertyDefinition, ClassDefinition, \
    ImportNames, ImportSource, Except, Expression, Attribute


class VariableAnalysis:
    """
    Provides information about the variables defined in an AST node. This information is supposed to be used by
    the translator and comprises
    - Which variables in the node are free variables, not *declared* inside the node?
    - Which variables can definitely be regarded as functional, i.e. are never written after they have been read? Note
      that this analysis cannot possibly decide this question accurately, but gives a safe underapproximation.
    """

    def __init__(self, statement, dec):
        """
        Analyses the variables in a sequence of AST nodes.
        :param dec: The dict returned from the Validator.
        :param statement: The Statement node to analyse as an executed sequence.
        """
        self._free = dict()
        self._free_in_proc = set()
        declared, _, _, nonfunctional, _ = self._analyse_statement(statement, dec)
        self._declared = {v: v not in nonfunctional for v in declared}

        self._unsafeonstack = nonfunctional & self._free_in_proc
        del self._free_in_proc

    def analyse_expression(self, node, dec, acc=None):
        """
        Analyses an expression node.
        :param node: An ExpressionNode.
        :param dec: A dict mapping AST nodes to decorations.
        :param acc: A dict into which variables discovered by this call are to be added.
        :return: A dict mapping variables contained in the given expression to whether they are free variables of the
                 expression. If 'acc' is given, these variables will be added to it and acc will be returned.
                 Note that variables will be represented by their defining AST Node, obtained via 'dec'.
        """
        if acc is None:
            acc = set()
        if isinstance(node, Identifier):
            try: # Using occurrence
                acc.add(dec[node][1])
            except KeyError: # Declaring occurrence
                acc.add(node)
        elif isinstance(node, Attribute):
            return self.analyse_expression(node.value, dec, acc)
        else:
            for c in node.children:
                self.analyse_expression(c, dec, acc)
        return acc

    @staticmethod
    def _update(declared, written, read, nonfunctional, free, ds, ws, rs, ns, fs):
        """
        Given information about variables obtained by analysing a sequence of statements, updates this information
        on the basis of another statement.
        Given the current state of the analysis, and the result of analysing another statement, updates the state of
        the analysis.
        :param declared: The set of variables declared in the previous statements. Will be updated by this call.
        :param written: The set of variables written by the previous statements. Will be updated by this call.
        :param read: The set of variables read by the previous statements. Will be updated by this call.
        :param nonfunctional: The set of variables that could be determined to not be functional solely by inspecting
                              the previous statements. Will be updated by this call.
        :param free: The set of free variables in the previous statements. Will be updated by this call.
        :param ds: The variables declared in the newly analsed statement.
        :param ws: The variables written in the newly analysed statement.
        :param rs: The variables read in the newly analysed statement.
        :param ns: The set of variables that could be determined to not be functional solely by inspecting
                      the newly analysed statement.
        :param fs: The free variables of the newly analysed statement.
        """
        declared |= ds
        read |= rs
        nonfunctional |= (ws & read) | ns
        written |= ws
        free |= fs - declared

    def _analyse_statement(self, node, dec):
        """
        Analyses a statement, updating the information collections in this instance.
        :param node: A Statement to analyse.
        :param dec: A dict mapping AST nodes to decorations.
        :return: A tuple (declared, written, read, nonfunctional, free) of iterables, where
                 'declared' is the set of variables declared in the given statements.
                'written' is the set of variables written by the given statement.
                'read' is the set of variables read by the given statement.
                'nonfunctional' is the set of variables that could be determined to not be functional solely by inspecting
                                the given statement.
                'free' is the set of free variables in the given statement.
        """

        declared = set()
        written = set()
        read = set()
        nonfunctional = set()
        free = set()

        empty = set()

        if node is None or isinstance(node, (Pass, Break, Continue)):
            pass
        elif isinstance(node, (ExpressionStatement, Return, Raise)):
            fs = self.analyse_expression(node, dec)
            VariableAnalysis._update(declared, written, read, nonfunctional, free, empty, empty, fs, empty, fs)
        elif isinstance(node, VariableDeclaration):
            ds = self.analyse_expression(node.pattern, dec)
            if node.expression is None:
                VariableAnalysis._update(declared, written, read, nonfunctional, free, ds, empty, empty, empty, empty)
            else:
                rs = self.analyse_expression(node.expression, dec)
                VariableAnalysis._update(declared, written, read, nonfunctional, free, ds, ds, rs, empty, rs)
        elif isinstance(node, Assignment):
            ws = self.analyse_expression(node.target, dec)
            rs = self.analyse_expression(node.value, dec)
            VariableAnalysis._update(declared, written, read, nonfunctional, free, empty, ws, rs, ws & rs, ws | rs)
        elif isinstance(node, Block):
            for s in node.children:
                ds, ws, rs, ns, fs = self._analyse_statement(s, dec)
                VariableAnalysis._update(declared, written, read, nonfunctional, free, ds, ws, rs, ns, fs)
        elif isinstance(node, Conditional):
            rs = self.analyse_expression(node.condition, dec)
            VariableAnalysis._update(declared, written, read, nonfunctional, free, empty, empty, rs, empty, rs)
            ds1, ws1, rs1, ns1, fs1 = self._analyse_statement(node.consequence, dec)
            ds2, ws2, rs2, ns2, fs2 = self._analyse_statement(node.alternative, dec)
            VariableAnalysis._update(declared, written, read, nonfunctional, free, ds1 | ds2, ws1 | ws2, rs1 | rs2, ns1 | ns2, fs1 | fs2)
        elif isinstance(node, While):
            rs = self.analyse_expression(node.condition, dec)
            VariableAnalysis._update(declared, written, read, nonfunctional, free, empty, empty, rs, empty, rs)
            ds, ws, rs, ns, fs = self._analyse_statement(node.body, dec)
            VariableAnalysis._update(declared, written, read, nonfunctional, free, ds, ws, rs, ns, fs)
            VariableAnalysis._update(declared, written, read, nonfunctional, free, empty, ws, rs, empty, fs)
        elif isinstance(node, For):
            rs = self.analyse_expression(node.iterable, dec)
            VariableAnalysis._update(declared, written, read, nonfunctional, free, empty, empty, rs, empty, rs)
            ds = self.analyse_expression(node.pattern, dec)
            VariableAnalysis._update(declared, written, read, nonfunctional, free, ds, ds, empty, empty, empty)
            ds, ws, rs, ns, fs = self._analyse_statement(node.body, dec)
            VariableAnalysis._update(declared, written, read, nonfunctional, free, ds, ws, rs, ns, fs)
            VariableAnalysis._update(declared, written, read, nonfunctional, free, empty, ws, rs, empty, fs)
        elif isinstance(node, Try):
            ds, ws, rs, us, fs = self._analyse_statement(node.body, dec)
            VariableAnalysis._update(declared, written, read, nonfunctional, free, ds, ws, rs, us, fs)
            for h in node.handlers:
                assert isinstance(h, Except)
                ds = self.analyse_expression(h.identifier, dec)
                VariableAnalysis._update(declared, written, read, nonfunctional, free, ds, ds, empty, empty, empty)
                ds, ws, rs, us, fs = self._analyse_statement(h.body, dec)
                VariableAnalysis._update(declared, written, read, nonfunctional, free, ds, ws, rs, us, fs)
            ds, ws, rs, us, fs = self._analyse_statement(node.final, dec)
            VariableAnalysis._update(declared, written, read, nonfunctional, free, ds, ws, rs, us, fs)
        elif isinstance(node, ProcedureDefinition):
            dsb, wsb, rsb, nsb, fsb = self._analyse_statement(node.body, dec)
            VariableAnalysis._update(declared, written, read, nonfunctional, free, {node.name}, empty, empty, empty, empty)
            VariableAnalysis._update(declared, written, read, nonfunctional, free, {*node.argnames, *dsb}, wsb | {node.name}, rsb, nsb | wsb, fsb - set(node.argnames))
            free.add(node.name)
            self._free_in_proc |= free
        elif isinstance(node, PropertyDefinition):
            dsb, wsb, rsb, nsb, fsb = self._analyse_statement(node.getter, dec)
            VariableAnalysis._update(declared, written, read, nonfunctional, free, dsb, wsb, rsb, nsb | wsb, fsb)

            dsb, wsb, rsb, nsb, fsb = self._analyse_statement(node.setter, dec)
            ds = {node.vname, *dsb}
            VariableAnalysis._update(declared, written, read, nonfunctional, free, ds, wsb, rsb, nsb | wsb, fsb - {node.vname})

            self._free_in_proc |= free
        elif isinstance(node, ClassDefinition):
            ds = {node.name}
            rs = node.bases
            VariableAnalysis._update(declared, written, read, nonfunctional, free, ds, ds, rs, empty, rs)
            for member in node.body:
                dsb, wsb, rsb, nsb, fsb = self._analyse_statement(member, dec)
                if isinstance(member, VariableDeclaration):
                    toremove = self.analyse_expression(member.pattern, dec)
                elif isinstance(member, ProcedureDefinition):
                    toremove = (member.name, )
                elif isinstance(member, PropertyDefinition):
                    toremove = (member.name, )
                else:
                    raise TypeError(f"Cannot analyse class members of type {type(member)}!")
                for v in toremove:
                    dsb.remove(v)
                    wsb.remove(v)
                    rsb.remove(v)
                    nsb.remove(v)
                VariableAnalysis._update(declared, written, read, nonfunctional, free, dsb, wsb, rsb, nsb, fsb)
        elif isinstance(node, ImportNames):
            ds = set(node.aliases.values())
            VariableAnalysis._update(declared, written, read, nonfunctional, free, ds, ds, empty, empty, empty)
        elif isinstance(node, ImportSource):
            ds = {node.alias}
            VariableAnalysis._update(declared, written, read, nonfunctional, free, ds, ds, empty, empty, empty)
        else:
            raise NotImplementedError()

        self._free[id(node)] = free

        return declared, written, read, nonfunctional, free

    @property
    def variables(self):
        """
        A mapping of all declared names to a boolean values, indicating if the declared name can safely be considered
        to be functional, i.e. it is never written after it has been read.
        """
        return dict(self._declared)

    def free(self, node):
        """
        Returns the set of free variables of the given node.
        :param node: The AST node the free variables of which are to be retrieved.
        :return: A set of ASTNode objects that identify the variables that are free in the given node.
        :exception TypeError: If the given node is a type for which this analysis does not record free variables.
        """
        if isinstance(node, Expression):
            raise ValueError("For computing the free variables of expression nodes, call self.analyse_expression!")
        return self._free[id(node)]

    def safe_on_stack(self, var):
        """
        Indicates if the given variable can safely be allocated directly on the call stack, or if it may be necessary
        to allocate it in a heap cell.
        :param var: The defining occurrence of the variable in question.
        :return: True if this analysis could reliably determine that stack allocation is sufficient, False otherwise.
        """
        return var not in self._unsafeonstack