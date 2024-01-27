from itertools import chain

from lang.spek.ast import Identifier, Pass, ExpressionStatement, Assignment, Return, Raise, Continue, Break, Block, \
    VariableDeclaration, Conditional, While, For, Try, ProcedureDefinition, PropertyDefinition, ClassDefinition, \
    ImportNames, ImportSource, Except


class VariableAnalysis:
    """
    Provides information about the variables defined in an AST node. This information is supposed to be used by
    the translator and comprises
    - Which variables in the node are free variables, not *declared* inside the node?
    - Which variables belong to a "volatile scope", i.e. are declared in a scope that could be left while the variable
      is still live?
    - Which variables can definitely be regarded as functional, i.e. are never written after they have been read? Note
      that this analysis cannot possibly decide this question accurately, but gives a safe underapproximation.
    """

    def __init__(self, node, dec):
        """
        Analyses the variables in a sequence of AST nodes.
        :param node: The AST node to analyse.
        :param dec: The dict returned from the Validator.
        """
        self._dec = dec
        self._analyse(node)


    def _analyse_expression(self, node, dec, acc=None):
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
            acc = {}
        if isinstance(node, Identifier):
            acc[dec[node][1]] = True
        else:
            for c in node.children:
                self._analyse_expression(c, dec, acc)
        return acc

    @staticmethod
    def _update(declared, written, read, nonfunctional, free, ds, ws, rs, ns, fs):
        """
        Given information about variables obtained by analysing a sequence of statements, updates this information
        on the basis of another statement.
        Given the current state of the analysis, and the result of analysing another statement, updates the state of
        the analysis.
        :param declared: Maps variables declared in the previous statements to a boolean value indicating if the allocation
                         context is a volatile one. Will be updated by this call.
        :param written: The set of variables written by the previous statements. Will be updated by this call.
        :param read: The set of variables read by the previous statements. Will be updated by this call.
        :param nonfunctional: The set of variables that could be determined to not be functional solely by inspecting
                              the previous statements. Will be updated by this call.
        :param free: The set of free variables in the previous statements. Will be updated by this call.
        :param ds: Maps variables declared in the newly analysed statement to a boolean value indicating if the allocation
                   context is a volatile one.
        :param ws: The variables written in the newly analysed statement.
        :param rs: The variables read in the newly analysed statement.
        :param ns: The set of variables that could be determined to not be functional solely by inspecting
                      the newly analysed statement.
        :param fs: The free variables of the newly analysed statement.
        """
        for var, vol in ds.items():
            declared[var] = vol
        read |= rs
        nonfunctional |= (ws & read) | ns
        written |= ws
        free |= fs - declared.keys()

    def _analyse_statement(self, node, dec):
        """
        Analyses a statement, updating the information collections in this instance.
        :param node: A Statement to analyse.
        :param dec: A dict mapping AST nodes to decorations.
        :return: A tuple (declared, written, read, nonfunctional, free) of iterables, where
                 'declared' maps variables declared in the given statements to a boolean value indicating if the allocation
                            context is a volatile one.
                'written' is the set of variables written by the given statement.
                'read' is the set of variables read by the given statement.
                'nonfunctional' is the set of variables that could be determined to not be functional solely by inspecting
                                the given statement.
                'free' is the set of free variables in the given statement.
        """

        declared = dict()
        written = set()
        read = set()
        nonfunctional = set()
        free = set()

        empty = set()

        if isinstance(node, (Pass, Break, Continue)):
            pass
        elif isinstance(node, (ExpressionStatement, Return, Raise)):
            fs = self._analyse_expression(node, dec).keys()
            VariableAnalysis._update(declared, written, read, nonfunctional, free, dict(), empty, fs, empty, fs)
        elif isinstance(node, VariableDeclaration):
            ds = {v: False for v in self._analyse_expression(node.pattern, dec).keys()}
            if node.expression is None:
                VariableAnalysis._update(declared, written, read, nonfunctional, free, ds, empty, empty, empty, empty)
            else:
                rs = self._analyse_expression(node.expression, dec).keys()
                VariableAnalysis._update(declared, written, read, nonfunctional, free, ds, ds.keys(), rs, empty, rs)
        elif isinstance(node, Assignment):
            ws = self._analyse_expression(node.target, dec).keys()
            rs = self._analyse_expression(node.value, dec).keys()
            VariableAnalysis._update(declared, written, read, nonfunctional, free, dict(), ws, rs, ws & rs, ws | rs)
        elif isinstance(node, Block):
            for s in node.children:
                ds, ws, rs, ns, fs = self._analyse_statement(s, dec)
                VariableAnalysis._update(declared, written, read, nonfunctional, free, ds, ws, rs, ns, fs)
        elif isinstance(node, Conditional):
            rs = self._analyse_expression(node.condition, dec).keys()
            VariableAnalysis._update(declared, written, read, nonfunctional, free, dict(), empty, rs, empty, rs)
            ds1, ws1, rs1, ns1, fs1 = self._analyse_statement(node.consequence, dec)
            ds2, ws2, rs2, ns2, fs2 = self._analyse_statement(node.consequence, dec)
            VariableAnalysis._update(declared, written, read, nonfunctional, free, ds1 | ds2, ws1 | ws2, rs1 | rs2, ns1 | ns2, fs1 | fs2)
        elif isinstance(node, While):
            rs = self._analyse_expression(node.condition, dec).keys()
            VariableAnalysis._update(declared, written, read, nonfunctional, free, dict(), empty, rs, empty, rs)
            ds, ws, rs, ns, fs = self._analyse_statement(node.body, dec)
            VariableAnalysis._update(declared, written, read, nonfunctional, free, ds, ws, rs, ns, fs)
            VariableAnalysis._update(declared, written, read, nonfunctional, free, dict(), ws, rs, empty, fs)
        elif isinstance(node, For):
            rs = self._analyse_expression(node.iterable, dec).keys()
            VariableAnalysis._update(declared, written, read, nonfunctional, free, dict(), empty, rs, empty, rs)
            ds = self._analyse_expression(node.pattern, dec).keys()
            VariableAnalysis._update(declared, written, read, nonfunctional, free, {d: True for d in ds}, ds, empty, empty, empty)
            ds, ws, rs, ns, fs = self._analyse_statement(node.body, dec)
            VariableAnalysis._update(declared, written, read, nonfunctional, free, ds, ws, rs, ns, fs)
            VariableAnalysis._update(declared, written, read, nonfunctional, free, dict(), ws, rs, empty, fs)
        elif isinstance(node, Try):
            ds, ws, rs, us, fs = self._analyse_statement(node.body, dec)
            VariableAnalysis._update(declared, written, read, nonfunctional, free, ds, ws, rs, us, fs)
            for h in node.handlers:
                assert isinstance(h, Except)
                ds = self._analyse_expression(h.identifier, dec).keys()
                VariableAnalysis._update(declared, written, read, nonfunctional, free, {d: True for d in ds}, ds, empty, empty, empty)
                ds, ws, rs, us, fs = self._analyse_statement(h.body, dec)
                VariableAnalysis._update(declared, written, read, nonfunctional, free, ds, ws, rs, us, fs)
            ds, ws, rs, us, fs = self._analyse_statement(node.final, dec)
            VariableAnalysis._update(declared, written, read, nonfunctional, free, ds, ws, rs, us, fs)
        elif isinstance(node, ProcedureDefinition):
            dsb, wsb, rsb, nsb, fsb = self._analyse_statement(node.body, dec)
            self._pfree[node] = fsb - node.argnames
            ds = {node.name: False}
            for d in chain(node.argnames, dsb):
                ds[d] = True
            VariableAnalysis._update(declared, written, read, nonfunctional, free, ds, wsb | {node.name}, rsb, nsb | wsb, fsb - {node.name, *node.argnames})
        elif isinstance(node, PropertyDefinition):
            dsb, wsb, rsb, nsb, fsb = self._analyse_statement(node.getter, dec)
            self._pfree[node.getter] = fsb
            ds = {d: True for d in dsb}
            VariableAnalysis._update(declared, written, read, nonfunctional, free, ds, wsb, rsb, nsb | wsb, fsb)

            dsb, wsb, rsb, nsb, fsb = self._analyse_statement(node.setter, dec)
            self._pfree[node] = fsb - {node.vname}
            ds = {d: True for d in chain([node.vname], dsb)}
            VariableAnalysis._update(declared, written, read, nonfunctional, free, ds, wsb, rsb, nsb | wsb, fsb - {node.vname})
        elif isinstance(node, ClassDefinition):

            # TODO: Treat the class variable like a Variable declaration.
            # TODO: In the body there can only be 3 types of statements:
            #       instance variable declarations, method declarations and property declarations.
            #       These may need to be treated specially, because of the class context.

        elif isinstance(node, (ImportNames, ImportSource)):
            # TODO: Names defined here need to be treated like VariableDeclarations.
        else:
            raise NotImplementedError()

        return declared, written, read, nonfunctional, free


    def functional(self, node):
        """
        Returns a subset of the variables allocated in the given node that can be identified as functional, i.e.
        where it can be deduced that the first read to the variable happens after the last write.
        :param node: The AST node that should be searched for functional variables.
        :return: A set of ASTNode objects that identify the functional variables.
        """
        # TODO: Implement this, as part of the "big recursive pass"
        #       Erst einmal setzten wir die Variable auf "nicht gelesen". Wenn wir einen Lesezugriff finden, setzen wir sie auf "gelesen". Wenn wir einen Schreibzugriff finden, zu dessen Zeit sie schon gelesen war, ist sie nicht mehr funktional.

    def volatile(self, node):
        """
        Returns the set of variables that are declared inside the given node, and belong to scopes that might be left
        while the variables are still alive.
        :param node: The AST node that should be searched for volatile variables.
        :return: A set of ASTNode objects that identify the volatile variables.
        """
        # TODO: Implement this, as part of the "big recursive pass"

    def free(self, node):
        """
        Returns the set of free variables of the given node.
        :param node: The AST node the free variables of which are to be retrieved.
        :return: A set of ASTNode objects that identify the variables that are free in the given node.
        :exception TypeError: If the given node is a type for which this analysis does not record free variables.
        """
        # TODO: Implement this, as part of the "big recursive pass". It needs to work only for *some* node types!