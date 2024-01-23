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


    def _analyse_statement(self, volatile_context, unread, node, dec):
        """
        Analyses a statement, updating the information collections in this instance.
        :param volatile_context: A boolean value specifying if the statement is in a context in which local variables
                                 would be allocated in a 'volatile context', i.e. a stack frame that might be deallocated
                                 code objects constructed as part of the statement execution are being executed.
        :param node: A Statement.
        :param unread: The set of available variables that have not been read yet.
        :param dec: A dict mapping AST nodes to decorations.
        :return: A triple (declared, written, read, free) of iterables that hold the variables written and read by this statement,
                 as well as the free variables of this statement.
        """

        if isinstance(node, (Pass, Break, Continue)):
            return tuple(), tuple(), tuple(), tuple()
        elif isinstance(node, (ExpressionStatement, Return, Raise)):
            vars = tuple(self._analyse_expression(node, dec).keys())
            return tuple(), tuple(), vars, vars
        elif isinstance(node, VariableDeclaration):
            declared = tuple(self._analyse_expression(node.pattern, dec).keys())
            self._functionals += declared
            if volatile_context:
                self._volatiles += declared
            read = tuple(self._analyse_expression(node.expression, dec).keys())
            return declared, declared, read, read - declared
        elif isinstance(node, Assignment):
            written = tuple(self._analyse_expression(node.target, dec).keys())
            vars = tuple(self._analyse_expression(node.value, dec).keys())
            return tuple(), written, vars, written + vars
        elif isinstance(node, Block):
            declared = set()
            written = set()
            read = set()
            free = ()
            unread = set(unread)
            for s in node.children:
                ds, ws, rs, fs = self._analyse_statement(volatile_context, unread, s, dec)
                for v in ws - unread:
                    self._functional -= v
                unread -= rs
                unread += ds
                read += rs
                free += fs - declared
                declared += ds
                written += ws
            return declared, written, read, free
        elif isinstance(node, Conditional):
            declared = set()
            written = set()
            read = set()
            free = ()
            unread = set(unread)

            vars_condition = self._analyse_expression(node.condition, dec).keys()
            read += vars_condition
            free += vars_condition
            unread -= vars_condition

            # TODO: Continue here, with consequence and alternative, like in the Block case!

            return declared, written, read, free
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