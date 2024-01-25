from lang.spek.ast import Identifier, Pass, ExpressionStatement, Assignment, Return, Raise, Continue, Break, Block, \
    VariableDeclaration, Conditional


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

    def _update_analysis(self, functional, volatile, declared, written, read, free, unread, ds, ws, rs, fs):
        """
        Given the current state of the analysis, and the result of analysing another statement, updates the state of
        the analysis.
        :param functional: The set of variables that so far are considered functional.
        :param volatile: The set of variables that are considered to be allocated in a volatile context. If the newly
                         analysed statement is declaring variables in a non-volatile context, None must be given.
        :param declared: The set of variables declared so far.
        :param written: The set of variables that were written so far.
        :param read: The set of variables that were read so far.
        :param free: The set of variables that are considered free so far.
        :param unread: The set of variables that were not read so far.
        :param ds: The variables declared in the newly analysed statement.
        :param ws: The variables written in the newly analysed statement.
        :param rs: The variables read in the newly analysed statement.
        :param fs: The free variables of the newly analysed statement.
        """
        functional += ds
        unread -= rs
        unread += ds
        functional -= ws - unread
        read += rs
        free += fs - declared
        declared += ds
        if volatile is not None:
            volatile += ds
        written += ws

    def _analyse_statement(self, functional, volatile, declared, written, read, free, unread, node, dec):
        """
        Analyses a statement, updating the information collections in this instance.
        :param functional: The set of variables that so far are considered functional.
        :param volatile: The set of variables that are considered to be allocated in a volatile context. If the newly
                         analysed statement is declaring variables in a non-volatile context, None must be given.
        :param declared: The set of variables declared so far.
        :param written: The set of variables that were written so far.
        :param read: The set of variables that were read so far.
        :param free: The set of variables that are considered free so far.
        :param unread: The set of variables that were not read so far.
        :param node: A Statement to analyse.
        :param dec: A dict mapping AST nodes to decorations.
        :return: A triple (declared, written, read, free) of iterables that hold the variables written and read by this statement,
                 as well as the free variables of this statement.
        """

        if isinstance(node, (Pass, Break, Continue)):
            pass
        elif isinstance(node, (ExpressionStatement, Return, Raise)):
            vars = tuple(self._analyse_expression(node, dec).keys())
            self._update_analysis(functional, volatile, declared, written, read, free, unread, [], [], vars, vars)
        elif isinstance(node, VariableDeclaration):
            ds = tuple(self._analyse_expression(node.pattern, dec).keys())
            if node.expression is None:
                rs = tuple()
            else:
                rs = tuple(self._analyse_expression(node.expression, dec).keys())
            self._update_analysis(functional, volatile, declared, written, read, free, unread, ds, ds, rs, rs)
        elif isinstance(node, Assignment):
            ws = tuple(self._analyse_expression(node.target, dec).keys())
            rs = tuple(self._analyse_expression(node.value, dec).keys())
            self._update_analysis(functional, volatile, declared, written, read, free, unread, [], ws, rs, ws + rs)
        elif isinstance(node, Block):
            for s in node.children:
                functional, volatile, declared, written, read, free, unread = self._analyse_statement(functional, volatile, declared, written, read, free, unread, s, dec)
        elif isinstance(node, Conditional):

            rs = self._analyse_expression(node.condition, dec).keys()
            self._update_analysis(functional, volatile, declared, written, read, free, unread, [], [], rs, rs)

            _, _, _, written1, read1, _, unread1 = self._analyse_statement(functional, volatile, declared, set(written), set(read), free, set(unread), node.consequence, dec)
            _, _, _, written2, read2, _, unread2 = self._analyse_statement(functional, volatile, declared, set(written), set(read), free, set(unread), node.alternative, dec)

            written += written1 + written2
            read += read1 + read2
            unread -= read1 + read2

        elif isinstance(node, While):
            self._analyse_statement(volatile_context, node.body, dec)
        elif isinstance(node, For):

            # TODO: The pattern variables need to be treated like VariableDeclarations!
            self._analyse_statement(volatile_context, node.body, dec)

        elif isinstance(node, Try):

            # TODO: The exception variables need to be treated like VariableDeclarations!

            self._analyse_statement(volatile_context, node.body, dec)
            self._analyse_statement(volatile_context, node.final, dec)
            for h in node.handlers:
                self._analyse_statement(volatile_context, h, dec)


        elif isinstance(node, ProcedureDefinition):

            # TODO: Any of the argument variables, or the procedure variable need to be treated like VariableDeclarations!

            self._analyse_statement(True, node.body, dec)

        elif isinstance(node, PropertyDefinition):

            # TODO: Like for procedures, the property name and the value argument of a setter need to be treated like VariableDeclarations!
            self._analyse_statement(True, node.getter, dec)
            self._analyse_statement(True, node.setter, dec)

        elif isinstance(node, ClassDefinition):

            # The class variable needs to be treated like a VariableDeclaration.
            self._analyse_statement(volatile_context, node.body, dec)

        elif isinstance(node, (ImportNames, ImportSource)):
            # TODO: Names defined here need to be treated like VariableDeclarations.
        else:
            raise NotImplementedError()

        return functional, volatile, declared, written, read, free, unread


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