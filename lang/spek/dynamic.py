from engine.core.atomic import type_object
from engine.core.data import VException, VStopIteration
from engine.stack.procedure import StackProcedure
from engine.stack.program import ProgramLocation
from lang.modules import ModuleSpecification
from lang.spek.chains import Chain
from lang.spek.data import terms
from lang.spek.data.exceptions import JumpType
from lang.spek.data.references import ReturnValueReference, ExceptionReference, FrameReference, \
    AbsoluteFrameReference
from lang.spek.data.terms import ComparisonOperator, BooleanBinaryOperator, CRef, UnaryOperator, Read, NewDict, \
    CTerm, CString, CNone, Callable, CInt, Project, NewCellReference, Iter, NewCell
from lang.spek.scopes import ScopeStack, ExceptionScope, ProcedureScope, LoopScope, ClassScope, ModuleScope
from lang.spek.vanalysis import VariableAnalysis
from lang.translator import Translator
from util import check_type
from .ast import Pass, Constant, Identifier, Attribute, Tuple, Projection, Call, Launch, Await, Comparison, \
    BooleanBinaryOperation, UnaryOperation, ArithmeticBinaryOperation, ImportNames, ImportSource, \
    ExpressionStatement, Assignment, Block, Return, Raise, Break, \
    Continue, Conditional, While, For, Try, VariableDeclaration, ProcedureDefinition, \
    PropertyDefinition, ClassDefinition, List, Dict


def negate(bexp):
    return terms.UnaryOperation(UnaryOperator.NOT, bexp)


class JumpEmissionError(Exception):
    """
    This error indicates that emitting machine code for a jump statement is not possible.
    """
    pass


class Spektakel2Stack(Translator):
    """
    A translator that translates Spektakel AST nodes into stack programs.
    """

    def __init__(self, builtin):
        """
        Initializes a new translator.
        :param builtin: An iterable of BuiltinModuleSpecification objects that define identifiers that are to be
                        builtin, i.e. valid without any explicit definition or import.
        """
        super().__init__()
        self._scopes = ScopeStack()
        self._vanalysis = None
        self._builtin = list(builtin)

    def declare_pattern(self, chain, pattern, on_error, acc=None, **kwargs):
        """
        Statically declares new variable names for an entire pattern of names.
        Depending on the context the names will be declared as stack frame
        variables, or as a namespace entries. The new variables are recorded for the given pattern, such that they can
        easily be retrieved later.
        :param chain: The Chain to which the instructions for allocating the new variables should be appended.
        :param kwargs: Arguments to ScopeStack.declare.
        :param on_error: The Chain to which control should be transferred if the allocation code fails.
        :param pattern: The Expression node holding the pattern expression for which to allocate new variables.
        :return: An iterable of Terms, that evaluate to *References* for the declared variables.
        """

        if acc is None:
            acc = []

        if pattern is None:
            acc.append(self._scopes.declare(chain, None, False, on_error, **kwargs))
        elif isinstance(pattern, str):
            acc.append(self._scopes.declare(chain, pattern, False, on_error, **kwargs))
        elif isinstance(pattern, Identifier):
            acc.append(self._scopes.declare(chain, pattern, not self._vanalysis.safe_on_stack(pattern), on_error, **kwargs))
        elif pattern.assignable:
            for c in pattern.children:
                self.declare_pattern(chain, c, on_error, **kwargs, acc=acc)
        else:
            raise TypeError("Patterns to be declared must only contain assignable nodes!")

        return acc

    def _get_method_class(self):
        """
        If the scope stack indicates that the translator is currently emitting code for an instance method,
        this method returns a term that evaluates to the type for which the method was defined.
        Otherwise this method returns None.
        """
        for scope in self._scopes:
            if isinstance(scope, ProcedureScope) and isinstance(scope.parent, ClassScope):
                return Read(NewCellReference(CRef(FrameReference(0))))
        return None

    def emit_assignment(self, chain, pattern, dec, term, on_error, declaring=False):
        """
        Emits VM code for assigning the result of an expression evaluation to a pattern.
        :param chain: The chain to which the assignment should be appended.
        :param pattern: An Expression to which a value should be assigned.
        :param dec: A dict mapping AST nodes to decorations.
        :param term: The term the result of which is to be assigned.
        :param on_error: The chain that execution should jump to in case of an error.
        :param declaring: Specifies if this assignment is part of a declaration, in which case it is assumed that
                          the given pattern is a *defining* occurrence of the declared name, not a *using* one.
                          The difference between these cases is that *using* occurrences will be mapped to defining
                          ones first, before the runtime reference for them can be retrieved.
        :return: A pair (refs, chain), where refs is a nested iterable of references that represent the assignment
                 targets and 'chain' is the chain with which execution is to be continued after the call.
                 ref will contain 'None' for targets that are not local variables.
        """

        if isinstance(pattern, Identifier):
            if not declaring:
                pattern = dec[pattern][1]
            r = self._scopes.retrieve(pattern)
            chain.append_update(r, term, on_error)
            return r, chain
        elif isinstance(pattern, Tuple):
            # FIXME: What we are doing here will not work if t represents a general iterable! For that we would
            #       need to call a procedure first that turns it into a sequence.
            refs = []
            for idx, c in enumerate(pattern.children):
                r, chain = self.emit_assignment(chain, c, dec, Read(terms.Project(term, terms.CInt(idx))), on_error, declaring=declaring)
                refs.append(r)
            return tuple(refs), chain
        elif isinstance(pattern, Projection):
            target, chain = self.translate_expression(chain, pattern.value, dec, on_error)
            index, chain = self.translate_expression(chain, pattern.index, dec, on_error)
            chain.append_update(Project(target, index), term, on_error)
            return None, chain
        elif isinstance(pattern, Attribute):
            # Python's "Descriptor How-To Guide"
            # (https://docs.python.org/3/howto/descriptor.html#overview-of-descriptor-invocation)
            # lists the following procedure for attribute lookup:
            # def object_getattribute(obj, name):
            #     "Emulate PyObject_GenericGetAttr() in Objects/object.c"
            #     null = object()
            #     objtype = type(obj)
            #     cls_var = find_name_in_mro(objtype, name, null)
            #     descr_get = getattr(type(cls_var), '__get__', null)
            #     if descr_get is not null:
            #         if (hasattr(type(cls_var), '__set__')
            #             or hasattr(type(cls_var), '__delete__')):
            #             return descr_get(cls_var, obj, objtype)     # data descriptor
            #     if hasattr(obj, '__dict__') and name in vars(obj):
            #         return vars(obj)[name]                          # instance variable
            #     if descr_get is not null:
            #         return descr_get(cls_var, obj, objtype)         # non-data descriptor
            #     if cls_var is not null:
            #         return cls_var                                  # class variable
            #     raise AttributeError(name)

            # We do not have general descriptors, but we have properties (which are data descriptors) and we have
            # methods (which are non-data descriptors). Hence for us the procedure above becomes this:

            a, chain = self.translate_expression(chain, pattern.value, dec, on_error)

            r, = self.declare_pattern(chain, None, on_error)
            dclass = self._get_method_class()
            chain.append_update(r, terms.StoreAttrCase(a, pattern.name.name, dclass=dclass), on_error)

            tr = Read(r)
            csetter = terms.UnaryPredicateTerm(terms.UnaryPredicate.ISCALLABLE, tr)
            cexception = terms.UnaryPredicateTerm(terms.UnaryPredicate.ISEXCEPTION, tr)
            cupdate = negate(terms.BooleanBinaryOperation(BooleanBinaryOperator.OR, csetter, cexception))

            setter = Chain()
            update = Chain()
            exception = Chain()
            successor = Chain()
            chain.append_guard({csetter: setter, cupdate: update, cexception: exception}, on_error)

            _, setter = self.emit_call(setter, Read(r), [term], on_error)
            setter.append_jump(successor)

            update.append_update(tr, term, on_error)
            update.append_jump(successor)

            exception.append_update(CRef(ExceptionReference()), tr, on_error)
            exception.append_jump(on_error)

            return None, successor

            # TODO: Implement this for 'super', see https://docs.python.org/3/howto/descriptor.html#invocation-from-super
            #       and https://www.python.org/download/releases/2.2.3/descrintro/#cooperation
        elif pattern.assignable:
            raise NotImplementedError("Assignment to patterns of type {} "
                                      "has not been implemented yet!".format(type(pattern)))
        else:
            raise TypeError("The pattern to which a value is assigned must be an assignable expression!")

    def emit_import(self, chain, spec, subnames, name, mapping, on_error):
        """
        Emits code for an import.
        :param chain: The chain to which the import should be appended.
        :param spec: The ModuleSpecification for the module to import.
        :param name: The name the imported module should be bound to, unless the name is None.
        :param subnames: The chain of submodule names to follow from the root module. This must be an iterable of
                         strings, that can be empty.
        :param mapping: A mapping from string names to be defined by this import statement to string names defined
                        in the imported module.
        :param on_error: The chain that execution should jump to in case of an error.
        :return: The chain with which execution is to be continued after the call.
        """

        check_type(spec, ModuleSpecification)

        module = spec.resolve()

        mproc = StackProcedure(0, ProgramLocation(module, 0))
        m, chain = self.emit_call(chain, Read(CRef(AbsoluteFrameReference(0, 0, 1))),
                                  [CTerm(mproc)], on_error)

        for a in subnames:
            m = terms.Project(m, CString(a))

        if name is not None:
            r, = self.declare_pattern(chain, name, on_error)
            chain.append_update(r, m, on_error)

        for name, member in mapping.items():
            r, = self.declare_pattern(chain, name, on_error)
            chain.append_update(r, Read(Project(m, CString(member))), on_error)

        return chain

    def emit_call(self, chain, callee, args, on_error):
        """
        Emits VM code for a procedure call.
        :param chain: The chain to which the call should be appended.
        :param callee: A Term object representing the procedure to be called.
        :param args: An iterable of term objects representing the arguments to the call.
        :param on_error: The chain that execution should jump to in case of an error.
        :return: A pair (t, c), where t is the term representing the return value of the call and c is the chain
                 in which execution is to be continued after the call.
        """

        chain.append_push(Callable(callee), args, on_error)

        successor = Chain()
        noerror = terms.Comparison(ComparisonOperator.EQ, Read(CRef(ExceptionReference())), terms.CNone())
        chain.append_guard({negate(noerror): on_error, noerror: successor}, on_error)

        rv, = self.declare_pattern(successor, None, on_error)
        rr = CRef(ReturnValueReference())
        successor.append_update(rv, Read(rr), on_error)
        return Read(rv), successor

    def translate_expression(self, chain, node, dec, on_error):
        """
        Generates code that evaluates the given AST expression.
        :param chain: The chain that the generated code should be appended to.
        :param node: An AST node representing an expression.
        :param dec: A dict mapping AST nodes to decorations.
        :parma on_error: The Chain to jump to in case of errors.
        :return: A pair (t, c), where
                 t is a term representing the result of the evaluation of the given expression. This term will evaluate
                 to the result of the evaluation of the expression, even if code for evaluating other expressions
                 is executed first.
                 c is the chain in which execution is to be continued after evaluation of the expression.
        """

        if isinstance(node, Constant):
            value = dec[node]
            if isinstance(value, bool):
                return terms.CBool(value), chain
            elif isinstance(value, str):
                return terms.CString(value), chain
            elif value is None:
                return terms.CNone(), chain
            elif isinstance(value, int):
                return terms.CInt(value), chain
            elif isinstance(value, float):
                return terms.CFloat(value), chain
            else:
                raise NotImplementedError("Translation of constant expressions of type {}"
                                          " has not been implemented!".format(type(value)))
        elif isinstance(node, Identifier):
            r, = self.declare_pattern(chain, None, on_error)
            chain.append_update(r, Read(self._scopes.retrieve(dec[node][1])), on_error)
            return Read(r), chain
        elif isinstance(node, Attribute):
            v, chain = self.translate_expression(chain, node.value, dec, on_error)

            r, = self.declare_pattern(chain, None, on_error)
            dclass = self._get_method_class()
            chain.append_update(r, terms.LoadAttrCase(v, node.name.name, dclass=dclass), on_error)

            cgetter = Read(terms.Project(Read(r), CInt(0)))

            getter, dvalue = Chain(), Chain()
            successor = Chain()
            chain.append_guard({cgetter: getter, negate(cgetter): dvalue}, on_error)

            v, getter = self.emit_call(getter, Read(terms.Project(Read(r), CInt(1))), [], on_error)
            getter.append_update(r, v, on_error)
            getter.append_jump(successor)

            dvalue.append_update(r, Read(terms.Project(Read(r), CInt(1))), on_error)
            dvalue.append_jump(successor)

            return Read(r), successor

            # TODO: Implement this for 'super', see https://docs.python.org/3/howto/descriptor.html#invocation-from-super
            #       and https://www.python.org/download/releases/2.2.3/descrintro/#cooperation
        elif isinstance(node, Call):
            callee, chain = self.translate_expression(chain, node.callee, dec, on_error)
            args = []
            for a in node.arguments:
                v, chain = self.translate_expression(chain, a, dec, on_error)
                args.append(v)
            return self.emit_call(chain, callee, args, on_error)
        elif isinstance(node, Launch):
            call = node.work
            callee, chain = self.translate_expression(chain, call.callee, dec, on_error)
            args = []
            for a in call.arguments:
                v, chain = self.translate_expression(chain, a, dec, on_error)
                args.append(v)
            chain.append_launch(Callable(callee), args, on_error)
            t, = self.declare_pattern(chain, None, on_error)
            chain.append_update(t, Read(CRef(ReturnValueReference())), on_error)
            return Read(t), chain
        elif isinstance(node, Await):
            a, chain = self.translate_expression(chain, node.awaited, dec, on_error)
            successor = Chain()
            complete = terms.UnaryPredicateTerm(terms.UnaryPredicate.ISTERMINATED, a)
            chain.append_guard({complete: successor}, on_error)
            r, = self.declare_pattern(chain, None, on_error)
            successor.append_update(r, terms.AwaitedResult(a), on_error)
            return Read(r), successor
        elif isinstance(node, Projection):
            target, chain = self.translate_expression(chain, node.value, dec, on_error)
            index, chain = self.translate_expression(chain, node.index, dec, on_error)
            r, = self.declare_pattern(chain, None, on_error)
            chain.append_update(r, Read(Project(target, index)), on_error)
            return Read(r), chain
        elif isinstance(node, UnaryOperation):
            arg, chain = self.translate_expression(chain, node.operand, dec, on_error)
            return terms.UnaryOperation(node.operator, arg), chain
        elif isinstance(node, ArithmeticBinaryOperation):
            left, chain = self.translate_expression(chain, node.left, dec, on_error)
            right, chain = self.translate_expression(chain, node.right, dec, on_error)
            return terms.ArithmeticBinaryOperation(node.operator, left, right), chain
        elif isinstance(node, Comparison):
            left, chain = self.translate_expression(chain, node.left, dec, on_error)
            right, chain = self.translate_expression(chain, node.right, dec, on_error)
            return terms.Comparison(node.operator, left, right), chain
        elif isinstance(node, BooleanBinaryOperation):
            # Like in Python, we want AND and OR to be short-circuited. This means that we require some control
            # flow in order to possibly skip the evaluation of the right operand.

            v, = self.declare_pattern(chain, None, on_error)
            left, chain = self.translate_expression(chain, node.left, dec, on_error)
            chain.append_update(v, left, on_error)

            rest = Chain()
            successor = Chain()

            if node.operator == BooleanBinaryOperator.AND:
                skip = negate(Read(v))
            elif node.operator == BooleanBinaryOperator.OR:
                skip = Read(v)
            else:
                raise ValueError(f"Cannot handle {node.operator}!")

            chain.append_guard({skip: successor, negate(skip): rest}, on_error)

            right, rest = self.translate_expression(rest, node.right, dec, on_error)
            rest.append_update(v, terms.BooleanBinaryOperation(node.operator, Read(v), right), on_error)
            rest.append_jump(successor)
            return Read(v), successor
        elif isinstance(node, Tuple):
            cs = []
            for c in node.children:
                r, chain = self.translate_expression(chain, c, dec, on_error)
                cs.append(r)

            v, = self.declare_pattern(chain, None, on_error)
            chain.append_update(v, terms.NewTuple(*cs), on_error)
            return Read(v), chain
        elif isinstance(node, List):
            cs = []
            for c in node.children:
                r, chain = self.translate_expression(chain, c, dec, on_error)
                cs.append(r)

            v, = self.declare_pattern(chain, None, on_error)
            chain.append_update(v, terms.NewList(*cs), on_error)
            return Read(v), chain
        elif isinstance(node, Dict):
            items = []
            for k, v in node.items:
                k, chain = self.translate_expression(chain, k, dec, on_error)
                v, chain = self.translate_expression(chain, v, dec, on_error)
                items.append((k, v))

            v, = self.declare_pattern(chain, None, on_error)
            chain.append_update(v, terms.NewDict(items), on_error)
            return Read(v), chain

        else:
            raise NotImplementedError()

    def emit_return(self, on_error, chain=None):
        """
        Emits code for a return statement, under the assumption that the return value has already been set for the task.
        :param chain: The chain to emit the code to. If this is omitted, a new chain will be created.
        :param on_error: The chain to jump to in case of an error.
        :return: Either the given chain, or the newly created one (if no chain was given).
        """

        if chain is None:
            chain = Chain()

        # First reset the exception register. This is useful because we may call this procedure *after*
        # a finally clause, in cases where the finally clause gets entered because of a return statement. In those cases
        # the exception stored in the register is artificial and should not surface:
        eref = CRef(ExceptionReference())
        chain.append_update(eref, CNone(), on_error=on_error)

        # Walk over the block stack ("outwards"), until you hit either an exception block or arrive at the function body:
        for scope in self._scopes:
            if isinstance(scope, ExceptionScope):
                chain.append_update(eref, terms.NewJumpError(JumpType.RETURN), on_error=on_error)
                chain.append_jump(scope.finally_chain)
                return chain
            elif isinstance(scope, ProcedureScope):
                break

        # We made it to the function level without hitting an exception block.
        chain.append_update(eref, terms.CNone(), on_error=on_error)
        chain.append_pop(on_error)

        return chain

    def emit_raise(self, value, dec, on_error, chain=None):
        """
        Emits code for a break statement.
        :param chain: The chain to emit the code to. If this is omitted, a new chain will be created.
        :param on_error: The chain to jump to in case of an error.
        :return: Either the given chain, or the newly created one (if no chain was given).
        """

        if chain is None:
            chain = Chain()

        eref = CRef(ExceptionReference())
        if value is None:
            # Walk over the block stack ("outwards") to find the exception block this re-raise is contained in.
            for scope in self._scopes:
                if isinstance(scope, ExceptionScope):
                    chain.append_update(eref, Read(scope.exception_reference), on_error=on_error)
                    chain.append_jump(scope.finally_chain)
                    return chain

            raise JumpEmissionError("This code location must never be reached,"
                                    " because raise statements without an expression should only appear in except clauses!")
        else:
            e, chain = self.translate_expression(chain, value, dec, on_error)
            chain.append_update(eref, e, on_error)
            chain.append_jump(on_error)
            return chain

    def emit_break(self, on_error, chain=None):
        """
        Emits code for a break statement.
        :param chain: The chain to emit the code to. If this is omitted, a new chain will be created.
        :param on_error: The chain to jump to in case of an error.
        :return: Either the given chain, or the newly created one (if no chain was given).
        """

        if chain is None:
            chain = Chain()

        # First reset the exception register. This is useful because we may call this procedure *after*
        # a finally clause, in cases where the finally clause gets entered because of a continue statement.
        # In those cases the exception stored in the register is artificial and should not surface:
        eref = CRef(ExceptionReference())
        chain.append_update(eref, CNone(), on_error=on_error)
        # Walk over the block stack ("outwards"), until you hit either an exception block or a loop:
        for scope in self._scopes:
            if isinstance(scope, ExceptionScope):
                chain.append_update(eref, terms.NewJumpError(JumpType.BREAK), on_error=on_error)
                chain.append_jump(scope.finally_chain)
                return chain
            elif isinstance(scope, LoopScope):
                chain.append_update(eref, terms.CNone(), on_error=on_error)
                chain.append_jump(scope.successor_chain)
                return chain

        raise JumpEmissionError("This code location must never be reached,"
                             " because break statements cannot be emitted outside loops!")

    def emit_continue(self, on_error, chain=None):
        """
        Emits code for a continue statement.
        :param chain: The chain to emit the code to. If this is omitted, a new chain will be created.
        :param on_error: The chain to jump to in case of an error.
        :return: Either the given chain, or the newly created one (if no chain was given).
        """

        if chain is None:
            chain = Chain()

        # First reset the exception register. This is useful because we may call this procedure *after*
        # a finally clause, in cases where the finally clause gets entered because of a return statement. In those cases
        # the exception stored in the register is artificial and should not surface:
        eref = CRef(ExceptionReference())
        chain.append_update(eref, CNone(), on_error=on_error)
        # Walk over the block stack ("outwards"), until you hit either an exception block or a loop:
        for scope in self._scopes:
            if isinstance(scope, ExceptionScope):
                chain.append_update(eref, terms.NewJumpError(JumpType.CONTINUE), on_error=on_error)
                chain.append_jump(scope.finally_chain)
                return chain
            elif isinstance(scope, LoopScope):
                chain.append_update(eref, terms.CNone(), on_error=on_error)
                chain.append_jump(scope.head_chain)
                return chain

        raise JumpEmissionError("This code location must never be reached,"
                             " because continue statements cannot be emitted outside loops!")

    def _emit_procedure(self, chain, name, argnames, body, dec, on_error):
        """
        Emits code for a procedure declaration.
        :param name: The AST node representing the name of the procedure.
        :param argnames: A tuple of AST nodes representing the argument names of the procedure.
        :param body: The AST node representing the body of the procedure.
        :param dec:
        :param on_error:
        :return: A pair (v, c), where v is a Term representing the procedure object and c is the chain to which code
                 following the procedure definition can be appended.
        """

        if name is not None:
            self._scopes.declare(chain, name, not self._vanalysis.safe_on_stack(name), on_error)

        entryBlock = Chain()
        exitBlock = Chain()

        num_args = len(argnames)

        ccell = None
        if isinstance(self._scopes.top, ClassScope):
            ccell = self._scopes.top.defcell

        self._scopes.push(ProcedureScope(self._scopes.top))

        # Declare all free variables as local variables:
        tocopy = []
        if ccell:
            tocopy.append(Read(ccell))
            self.declare_pattern(entryBlock, None, on_error, initialize=False)

        for fname in self._vanalysis.free(body):
            if fname in argnames:
                continue
            r = self._scopes.retrieve(fname)
            if isinstance(r, NewCellReference):
                r = r.core
            tocopy.append(Read(r))
            self.declare_pattern(entryBlock, fname, on_error, initialize=False)

        # Declare the function arguments as local variables:
        for aname in argnames:
            self.declare_pattern(entryBlock, aname, on_error, initialize=False, cellify=not self._vanalysis.safe_on_stack(aname))

        bodyBlock = self.translate_statement(entryBlock, body, dec, exitBlock)
        bodyBlock.append_pop(exitBlock)
        del bodyBlock

        exitBlock.append_pop(exitBlock)

        f = terms.NewProcedure(num_args, tocopy, entryBlock.compile())

        self._scopes.pop()

        if name is None:
            return f, chain
        else:
            name, chain = self.emit_assignment(chain, name, dec, f, on_error, declaring=True)
            return name, chain

    def translate_statement(self, chain, node, dec, on_error):
        """
        Translates a statement into a StackProgram.
        :param chain: The chain to which to append the translation of the statement.
        :param node: An AST node representing a Statement.
        :param dec: A dict mapping AST nodes to decorations.
        :param on_error: The chain to jump to in case an (unhandled) error occurs during the execution of the translated
                         statement.
        :return: A Chain object that the instructions resulting from the translation of the statement will jump to
                 after completing the execution of the statement.
        """

        if isinstance(node, Pass):
            return chain
        elif isinstance(node, ExpressionStatement):
            _, chain = self.translate_expression(chain, node.expression, dec, on_error)
            # The previous line generated code for any side effects of the expression.
            # We do not really need to use the expression itself,
            # because its evaluation result is not to be bound to anything.
            return chain
        elif isinstance(node, Assignment):
            t, chain = self.translate_expression(chain, node.value, dec, on_error)
            _, chain = self.emit_assignment(chain, node.target, dec, t, on_error)
            return chain
        elif isinstance(node, Block):
            for s in node.children:
                chain = self.translate_statement(chain, s, dec, on_error)
            return chain
        elif isinstance(node, Return):
            if node.value is not None:
                r, chain = self.translate_expression(chain, node.value, dec, on_error)
                chain.append_update(CRef(ReturnValueReference()), r, on_error)
            self.emit_return(on_error, chain)
            return Chain()
        elif isinstance(node, Raise):
            self.emit_raise(node.value, dec, on_error, chain)
            return Chain()
        elif isinstance(node, Break):
            self.emit_break(on_error, chain)
            return Chain()
        elif isinstance(node, Continue):
            self.emit_continue(on_error, chain)
            return Chain()
        elif isinstance(node, Conditional):
            consequence = Chain()
            alternative = Chain()
            successor = Chain()
            condition, chain = self.translate_expression(chain, node.condition, dec, on_error)
            chain.append_guard({condition: consequence, negate(condition): alternative}, on_error)
            consequence = self.translate_statement(consequence, node.consequence, dec, on_error)
            consequence.append_jump(successor)
            if node.alternative is not None:
                alternative = self.translate_statement(alternative, node.alternative, dec, on_error)
            alternative.append_jump(successor)
            return successor
        elif isinstance(node, While):
            head_in = Chain()
            body = Chain()
            successor = Chain()
            chain.append_jump(head_in)
            condition, head_out = self.translate_expression(head_in, node.condition, dec, on_error)
            head_out.append_guard({condition: body, negate(condition): successor}, on_error)
            self._scopes.push(LoopScope(self._scopes.top, head_in, successor))
            body = self.translate_statement(body, node.body, dec, on_error)
            self._scopes.pop()
            body.append_jump(head_in)
            return successor
        elif isinstance(node, For):
            """
            A for loop is syntactic sugar for:
                it = xs.__iter__()
                while True:
                    try:
                        pattern = it.__next__()
                    except StopIteration:
                        break
                    <body>
            """
            iterable, chain = self.translate_expression(chain, node.iterable, dec, on_error)
            next, = self.declare_pattern(chain, None, on_error)
            chain.append_update(next, Read(terms.Project(terms.LoadAttrCase(Iter(iterable), "__next__"), CInt(1))), on_error)
            self.declare_pattern(chain, node.pattern, on_error)

            body_in = Chain()
            body = body_in
            successor = Chain()
            chain.append_jump(body_in)
            self._scopes.push(LoopScope(self._scopes.top, body_in, successor))
            stopper = Chain()
            element, body = self.emit_call(body, Callable(Read(next)), [], stopper)
            eref = CRef(ExceptionReference())
            stop = terms.IsInstance(Read(eref), CTerm(VStopIteration.intrinsic_type))
            stopper.append_guard({stop: successor, negate(stop): on_error}, on_error)
            successor.append_update(eref, terms.CNone(), on_error)
            _, body = self.emit_assignment(body, node.pattern, dec, element, on_error, declaring=True)
            body = self.translate_statement(body, node.body, dec, on_error)
            self._scopes.pop()
            body.append_jump(body_in)
            return successor
        elif isinstance(node, Try):
            handler = Chain()
            restoration = Chain()
            finally_head = Chain()
            successor = Chain()
            exception, = self.declare_pattern(handler, None, on_error)
            self._scopes.push(ExceptionScope(self._scopes.top, exception, finally_head))
            chain = self.translate_statement(chain, node.body, dec, handler)
            chain.append_jump(finally_head)

            # As the very first step, the exception variable of the task is cleared:
            eref = CRef(ExceptionReference())
            handler.append_update(exception, Read(eref), on_error)
            handler.append_update(eref, terms.CNone(), on_error)

            for h in node.handlers:
                sc = Chain()
                hc = Chain()
                if h.type is None:
                    handler.append_jump(hc)
                else:
                    t, handler = self.translate_expression(handler, h.type, dec, finally_head)
                    match = terms.IsInstance(Read(exception), t)
                    handler.append_guard({match: hc, negate(match): sc}, finally_head)

                if h.identifier is not None:
                    hex, = self.declare_pattern(hc, h.identifier, on_error)
                    hc.append_update(hex, Read(exception), on_error)
                hc = self.translate_statement(hc, h.body, dec, finally_head)
                hc.append_jump(finally_head)

                handler = sc

            # If none of the handlers apply, restore the exception variable and jump to the finally:
            handler.append_jump(restoration)

            restoration.append_update(eref, Read(exception), on_error)
            restoration.append_update(exception, terms.CNone(), on_error)
            restoration.append_jump(finally_head)

            self._scopes.pop()

            r = CRef(ReturnValueReference())

            if node.final is not None:
                # The finally clause first stashes the current exception and return value away:
                returnvalue, = self.declare_pattern(finally_head, None, on_error)
                finally_head.append_update(exception, Read(eref), on_error)
                finally_head.append_update(eref, terms.CNone(), on_error)
                finally_head.append_update(returnvalue, Read(r), on_error)
                finally_head.append_update(r, terms.CNone(), on_error)
                # Then it executes its body:
                finally_foot = self.translate_statement(finally_head, node.final, dec, on_error)
                # Then it restores the stashed exception and return value:
                finally_foot.append_update(r, Read(returnvalue), on_error)
                finally_foot.append_update(eref, Read(exception), on_error)
                finally_foot.append_update(returnvalue, terms.CNone(), on_error)
            else:
                finally_foot = finally_head

            # Then it decides where to jump to, depending on the exception that caused the finally to be entered:
            e = Read(eref)
            condition_return = terms.UnaryPredicateTerm(terms.UnaryPredicate.ISRETURN, e)
            condition_break = terms.UnaryPredicateTerm(terms.UnaryPredicate.ISBREAK, e)
            condition_continue = terms.UnaryPredicateTerm(terms.UnaryPredicate.ISCONTINUE, e)

            condition_exception = terms.BooleanBinaryOperation(BooleanBinaryOperator.AND, terms.IsInstance(e, CTerm(VException.intrinsic_type)),
                                                               terms.BooleanBinaryOperation(
                                                                   terms.BooleanBinaryOperator.AND, negate(condition_break),
                                                                   terms.BooleanBinaryOperation(BooleanBinaryOperator.AND, negate(condition_continue), negate(condition_return))))
            condition_termination = terms.Comparison(ComparisonOperator.IS, e, terms.CNone())

            alternatives = {condition_termination: successor,
                            condition_exception: on_error}
            for c, e in ((condition_return, self.emit_return),
                         (condition_break, self.emit_break),
                         (condition_continue, self.emit_continue)):
                try:
                    alternatives[c] = e(on_error)
                except JumpEmissionError:
                    continue
            finally_foot.append_guard(alternatives, on_error)

            return successor
        elif isinstance(node, VariableDeclaration):
            self.declare_pattern(chain, node.pattern, on_error)
            if node.expression is not None:
                t, chain = self.translate_expression(chain, node.expression, dec, on_error)
                _, chain = self.emit_assignment(chain, node.pattern, dec, t, on_error, declaring=True)
            return chain
        elif isinstance(node, ProcedureDefinition):
            _, chain = self._emit_procedure(chain, node.name, node.argnames, node.body, dec, on_error)
            return chain
        elif isinstance(node, PropertyDefinition):
            getter, chain = self._emit_procedure(chain, None, [node.gself], node.getter, dec, on_error)
            setter, chain = self._emit_procedure(chain, None, [node.sself, node.vname], node.setter, dec, on_error)
            # A property is a special kind of descriptor (see https://docs.python.org/3/glossary.html#term-descriptor).
            # A property object does not have private data. It only holds the getter and the setter. Both those
            # methods take an instance as argument and then read/write that.
            name, = self.declare_pattern(chain, node.name, on_error)
            chain.append_update(name, terms.NewProperty(getter, setter), on_error)
            return chain
        elif isinstance(node, ClassDefinition):
            super_classes = []
            for s_expression in node.bases:
                s_term, chain = self.translate_expression(chain, s_expression, dec, on_error)
                super_classes.append(s_term)

            if len(super_classes) == 0:
                super_classes.append(CTerm(type_object))

            c = self._scopes.declare(chain, node.name, True, on_error)

            self._scopes.push(ClassScope(self._scopes.top, c.core, c))
            # We create a new namespace dict and put it into the stack frame.
            chain.append_update(c, terms.NewDict({}), on_error)

            chain = self.translate_statement(chain, node.body, dec, on_error)

            self._scopes.pop()

            _, chain = self.emit_assignment(chain, node.name, dec, terms.NewClass(node.name.name, super_classes, Read(c)), on_error, declaring=True)

            if self._vanalysis.safe_on_stack(node.name):
                cc = self._scopes.declare(chain, node.name, False, on_error)
                chain.append_update(cc, Read(c), on_error)
            else:
                chain.append_update(c.core, NewCell(Read(c)), on_error)

            return chain

        elif isinstance(node, (ImportNames, ImportSource)):

            ms = check_type(dec[node.source], ModuleSpecification)
            subnames = list(map(str, node.source.identifiers[1:]))

            if isinstance(node, ImportSource):
                mapping = {}
                if node.alias is None:
                    if not (len(node.source.identifiers) == 1):
                        raise NotImplementedError("Code generation for a source import that contains dots has not been implemented!")
                    name = node.source.identifiers[0]
                else:
                    name = node.alias
            elif isinstance(node, ImportNames):
                if node.wildcard:
                    raise NotImplementedError("Compilation of wildcard imports has not been implemented!")
                mapping = {alias.name: name.name for name, alias in node.aliases.items()}
                name = None
            else:
                raise NotImplementedError("Code generation for nodes of type {}"
                                          " has not been implemented!".format(type(node)))

            return self.emit_import(chain, ms, subnames, name, mapping, on_error)
        else:
            raise NotImplementedError()

    def emit_preamble(self):
        """
        Emits code that is to run once at the beginning of execution.
        :return: A Chain object.
        """

        """ We generate code for this:
            
            var mcv = {}

            def ___import___(location):
                try:
                    return mcv[location]
                except KeyError:
                    m = ___call___(location, [Module()])
                    mcv[location] = m
                    return m
                    
            del mcv
        """

        preamble = Chain()
        panic = Chain()

        d, = self.declare_pattern(preamble, None, panic)
        d = AbsoluteFrameReference(0, 0, d.instance_key.index)
        preamble.append_update(CRef(d), NewDict([]), panic)

        self._scopes.push(ProcedureScope(self._scopes.top))
        imp_code = Chain()
        load1 = Chain()
        load2 = Chain()
        exit = Chain()
        l, = self.declare_pattern(imp_code, None, panic)

        r = CRef(ReturnValueReference())

        imp_code.append_update(r, Read(Project(Read(CRef(d)), Read(l))), load1)
        imp_code.append_pop(exit)
        load1.append_update(CRef(ExceptionReference()), CNone(), panic)
        load1.append_push(Callable(Read(l)), [], exit)
        error = terms.Comparison(ComparisonOperator.NEQ, Read(CRef(ExceptionReference())), terms.CNone())
        load1.append_guard({error: exit, negate(error): load2}, panic)
        load2.append_update(Project(Read(CRef(d)), Read(l)), Read(r), panic)
        load2.append_jump(exit)
        exit.append_pop(panic)
        self._scopes.pop()

        d = AbsoluteFrameReference(0, 0, 1)
        preamble.append_update(CRef(d), CTerm(StackProcedure(1, ProgramLocation(imp_code.compile(), 0))), panic)

        return preamble

    def translate_module(self, nodes, dec):
        """
        Generates code for an entire module.
        :param nodes: An iterable of statements that represent the code of the module.
        :param dec: A dict mapping AST nodes to decorations.
        :return: A Chain object.
        """

        # We assume that somebody put a fresh frame on the stack.

        self._vanalysis = VariableAnalysis(Block(nodes), dec)

        block = Chain()
        entry = block
        exit = Chain()

        # We create a new namespace dict and put it into the stack frame.
        block.append_update(CRef(FrameReference(0)), terms.NewDict([]), exit)

        # The code of a module assumes that there is 1 argument on the current stack frame, which is the Namespace object
        # that is to be populated. All allocations of local variables must actually be members of that Namespace object.
        self._scopes.push(ModuleScope())

        # Import the builtin names:
        for bms in self._builtin:
            block = self.emit_import(block, bms, [], None, {s: s for s in bms.symbols}, exit)

        # We execute the module code completely, which populates that namespace.
        for node in nodes:
            block = self.translate_statement(block, node, dec, exit)

        # Return the namespace. The preamble will store it somewhere.
        block.append_update(CRef(ReturnValueReference()), Read(CRef(FrameReference(0))), exit)

        block.append_pop(exit)
        exit.append_pop(exit)

        self._scopes.pop()

        return entry

    def translate(self, spec):
        """
        Translate a standalone program.
        :param spec: A ModuleSpecification to translate into a standalone program.
        :return: A Chain object.
        """
        self._scopes.push(ModuleScope(0))
        code = self.emit_preamble()
        on_error = Chain()
        on_error.append_pop(on_error)
        self.emit_import(code, spec, [],  None,{}, on_error)
        self._scopes.pop()
        return code