from engine.functional import terms
from engine.functional.reference import ReturnValueReference, ExceptionReference, FrameReference, \
    AbsoluteFrameReference
from engine.functional.terms import ComparisonOperator, BooleanBinaryOperator, TRef, UnaryOperator, Read, NewDict, \
    CTerm, Lookup, CString, CNone
from engine.functional.values import VReturnError, VBreakError, VContinueError, VDict, VProcedure
from engine.tasks.instructions import Launch
from engine.tasks.program import ProgramLocation
from lang.translator import Translator
from util import check_type
from .ast import Pass, Constant, Identifier, Attribute, Tuple, Projection, Call, Launch, Await, Comparison, \
    BooleanBinaryOperation, UnaryOperation, ArithmeticBinaryOperation, ImportNames, ImportSource, \
    ExpressionStatement, Assignment, Block, Return, Raise, Break, \
    Continue, Conditional, While, For, Try, VariableDeclaration, ProcedureDefinition, \
    PropertyDefinition, ClassDefinition
from .chains import Chain
from .scopes import ScopeStack, ExceptionScope, FunctionScope, LoopScope, ClassScope, ModuleScope
from .vanalysis import VariableAnalysis
from ..modules import ModuleSpecification


def negate(bexp):
    return terms.UnaryOperation(UnaryOperator.NOT, bexp)


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
        self._cells = None
        self._builtin = list(builtin)

    def declare_pattern(self, chain, pattern, on_error):
        """
        Statically declares new variable names for an entire pattern of names.
        Depending on the context the names will be declared as stack frame
        variables, or as a namespace entries. The new variables are recorded for the given pattern, such that they can
        easily be retrieved later.
        :param chain: The Chain to which the instructions for allocating the new variables should be appended.
        :param on_error: The Chain to which control should be transferred if the allocation code fails.
        :param pattern: The Expression node holding the pattern expression for which to allocate new variables.
        """

        if pattern is None:
            self._scopes.declare(chain, None, False, on_error)
        elif isinstance(pattern, Identifier):
            self._scopes.declare(chain, pattern, pattern in self._cells, on_error)
        elif pattern.assignable:
            for c in pattern.children:
                self.declare_pattern(chain, c, on_error)
        else:
            raise TypeError("Patterns to be declared must only contain assignable nodes!")

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
            r = self.decl2ref(pattern)
            chain.append_update(TRef(r), term, on_error)
            return r, chain
        elif isinstance(pattern, Tuple):
            # FIXME: What we are doing here will not work if t represents a general iterable! For that we would
            #       need to call a procedure first that turns it into a sequence.
            refs = []
            for idx, c in enumerate(pattern.children):
                r, chain = self.emit_assignment(chain, c, dec, terms.Project(term, terms.CInt(idx)), on_error, declaring=declaring)
                refs.append(r)
            return tuple(refs), chain
        elif isinstance(pattern, Projection):
            callee, chain = self.translate_expression(chain, Attribute(pattern.value, "__set_item__"), dec, on_error)
            index, chain = self.translate_expression(chain, pattern.index, dec, on_error)
            return None, self.emit_call(chain, callee, [index, term], on_error)
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

            r = self.declare_pattern(chain, None, on_error)
            chain.append_update(r, terms.StoreAttrCase(a, pattern.name), on_error)

            csetter = terms.UnaryPredicateTerm(terms.UnaryPredicate.ISCALLABLE, r)
            cexception = terms.UnaryPredicateTerm(terms.UnaryPredicate.ISEXCEPTION, r)
            cupdate = ~(csetter | cexception)

            setter = Chain()
            update = Chain()
            exception = Chain()
            successor = Chain()
            chain.append_guard({csetter: setter, cupdate: update, cexception: exception}, on_error)

            self.emit_call(setter, r, [term], on_error)
            setter.append_jump(successor)

            update.append_update(r, term, on_error)
            update.append_jump(successor)

            exception.append_update(ExceptionReference(), r, on_error)
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

        m, chain = self.emit_call(chain, Read(TRef(AbsoluteFrameReference(0, 0, 1))),
                                  [CTerm(ProgramLocation(module, 0))], on_error)

        m = m.children[0]

        for a in subnames:
            m = terms.Lookup(m, CString(a))

        if name is not None:
            chain.append_update(TRef(self.declare_pattern(chain, name, on_error)), m, on_error)

        for name, member in mapping.items():
            chain.append_update(TRef(self.declare_pattern(chain, name, on_error)), Read(Lookup(m, CString(member))), on_error)

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

        # Make sure that the right number of arguments is being used:
        call = Chain()
        argc_error = Chain()
        argc_error.append_update(TRef(ExceptionReference()), terms.NewTypeError("Wrong number of arguments for call!"), on_error)
        argc_error.append_jump(on_error)
        match = terms.Comparison(ComparisonOperator.EQ, terms.NumArgs(callee), terms.CInt(len(args)))
        chain.append_guard({match: call, negate(match): argc_error}, on_error)

        call.append_push(callee, args, on_error)

        successor = Chain()
        noerror = terms.Comparison(ComparisonOperator.EQ, terms.Read(TRef(ExceptionReference())), terms.CNone())
        call.append_guard({negate(noerror): on_error, noerror: successor}, on_error)

        rv = self.declare_pattern(successor, None, on_error)
        rr = ReturnValueReference()
        successor.append_update(TRef(rv), terms.Read(TRef(rr)), on_error)
        return Read(TRef(rv)), successor

    def translate_expression(self, chain, node, dec, on_error):
        """
        Translates an AST expression into a machine expression.
        :param node: An AST node representing an expression.
        :param dec: A dict mapping AST nodes to decorations.
        :return: A pair (t, c), where t is the term representing the result of expression evaluation and c is the chain
                 in which execution is to be continued after evaluation of the expression.
        """

        if isinstance(node, Constant):
            value = dec[node]
            if isinstance(value, bool):
                return (terms.CBool(True) if value == True else terms.CBool(False)), chain
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
            return Read(CTerm(self.decl2ref(dec[node][1]))), chain
        elif isinstance(node, Attribute):
            v, chain = self.translate_expression(chain, node.value, dec, on_error)

            r = self.declare_pattern(chain, None, on_error)
            chain.append_update(r, terms.LoadAttrCase(v, node.name), on_error)

            cgetter = terms.UnaryPredicateTerm(terms.UnaryPredicate.ISGETTER, r)

            getter = Chain()
            successor = Chain()
            chain.append_guard({cgetter: getter, ~cgetter: successor}, on_error)

            v, getter = self.emit_call(getter, r, [], on_error)
            getter.append_update(r, v, on_error)
            getter.append_jump(successor)

            return r, successor

            # TODO: Implement this for 'super', see https://docs.python.org/3/howto/descriptor.html#invocation-from-super
            #       and https://www.python.org/download/releases/2.2.3/descrintro/#cooperation
        elif isinstance(node, Call):
            args = []
            for a in node.arguments:
                v, chain = self.translate_expression(chain, a, dec, on_error)
                args.append(v)

            callee, chain = self.translate_expression(chain, node.callee, dec, on_error)
            return self.emit_call(chain, callee, args, on_error)
        elif isinstance(node, Launch):
            args = []
            for a in node.arguments:
                v, chain = self.translate_expression(chain, a, dec, on_error)
                args.append(v)
            callee, chain = self.translate_expression(chain, node.callee, dec, on_error)
            chain.append_launch(callee, args, on_error)
            t = self.declare_pattern(chain, None, on_error)
            chain.append_update(t, terms.Read(ReturnValueReference()), on_error)
            return t, chain
        elif isinstance(node, Await):
            t, chain = self.translate_expression(chain, node.process, dec, on_error)
            successor = Chain()
            complete = terms.UnaryPredicateTerm(terms.UnaryPredicate.ISTERMINATED, t)
            chain.append_guard({complete: successor}, on_error)

            successor = Chain()
            successor2 = Chain()
            noerror = terms.Comparison(ComparisonOperator.EQ, terms.Read(TRef(ExceptionReference())), terms.CNone())
            successor.append_guard({negate(noerror): on_error, noerror: successor2}, on_error)

            rv = TRef(self.declare_pattern(successor2, None, on_error))
            rr = TRef(ReturnValueReference())
            successor2.append_update(rv, terms.Read(rr), on_error)
            successor2.append_update(rr, terms.CNone(), on_error)
            return Read(rv), successor2
        elif isinstance(node, Projection):
            idx, chain = self.translate_expression(chain, node.index, dec, on_error)
            v, chain = self.translate_expression(chain, node.value, dec, on_error)
            callee, chain = self.translate_expression(chain, Attribute(v, "__get_item__"), dec, on_error)
            return self.emit_call(chain, callee, [idx], on_error)
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
            # Note: Like in Python, we want AND and OR to be short-circuited. This means that we require some control
            #       flow in order to possibly skip the evaluation of the right operand.

            v = TRef(self.declare_pattern(chain, None, on_error))
            left, chain = self.translate_expression(chain, node.left, dec, on_error)
            chain.append_update(v, left, on_error)

            rest = Chain()
            successor = Chain()

            if node.operator == BooleanBinaryOperator.AND:
                skip = negate(terms.Read(v))
            elif node.operator == BooleanBinaryOperator.OR:
                skip = terms.Read(v)
            else:
                skip = terms.CBool(False)

            chain.append_guard({skip: successor, negate(skip): rest}, on_error)

            right, rest = self.translate_expression(rest, node.right, dec, on_error)
            rest.append_update(v, terms.BooleanBinaryOperation(node.operator, terms.Read(v), right), on_error)
            rest.append_jump(successor)
            return terms.Read(v), successor
        elif isinstance(node, Tuple):
            cs = []
            for c in node.children:
                r, chain = self.translate_expression(chain, c, dec, on_error)
                cs.append(r)
            return terms.NewTuple(*cs), chain
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

        # Walk over the block stack ("outwards"), until you hit either an exception block or arrive at the function body:
        for scope in self._scopes:
            if isinstance(scope, ExceptionScope):
                chain.append_update(ExceptionReference(), terms.NewJumpError(VReturnError), on_error=on_error)
                chain.append_jump(scope.finally_chain)
                return chain
            elif isinstance(scope, FunctionScope):
                break

        # We made it to the function level without hitting an exception block.
        chain.append_update(TRef(ExceptionReference()), terms.CNone(), on_error=on_error)
        chain.append_pop()

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

        # Walk over the block stack ("outwards"), until you hit either an exception block or a loop:
        for scope in self._scopes:
            if isinstance(scope, ExceptionScope):
                chain.append_update(TRef(ExceptionReference()), terms.NewJumpError(VBreakError), on_error=on_error)
                chain.append_jump(scope.finally_chain)
                return Chain()
            elif isinstance(scope, LoopScope):
                chain.append_update(TRef(ExceptionReference()), terms.CNone(), on_error=on_error)
                chain.append_jump(scope.successor_chain)
                return Chain()

        raise AssertionError("This code location must never be reached,"
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

        # Walk over the block stack ("outwards"), until you hit either an exception block or a loop:
        for scope in self._scopes:
            if isinstance(scope, ExceptionScope):
                chain.append_update(TRef(ExceptionReference()), terms.NewJumpError(VContinueError), on_error=on_error)
                chain.append_jump(scope.finally_chain)
                return Chain()
            elif isinstance(scope, LoopScope):
                chain.append_update(TRef(ExceptionReference()), terms.CNone(), on_error=on_error)
                chain.append_jump(scope.head_chain)
                return Chain()

        raise AssertionError("This code location must never be reached,"
                             " because break statements cannot be emitted outside loops!")

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

        entryBlock = Chain()
        exitBlock = Chain()

        num_args = len(argnames)

        self._scopes.push(FunctionScope(self._scopes.top))

        # Declare the function arguments as local variables:
        for aname in argnames:
            self.declare_pattern(entryBlock, aname, on_error)

        bodyBlock = self.translate_statement(entryBlock, body, dec, exitBlock)
        bodyBlock.append_pop()
        del bodyBlock

        exitBlock.append_pop()

        f = terms.NewProcedure(num_args, entryBlock.compile())

        self._scopes.pop()

        if name is None:
            return f, chain
        else:

            try:
                self._scopes.retrieve(name)
            except KeyError:
                self._scopes.declare(chain, name, name in self._cells, on_error)
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
                chain.append_update(TRef(ReturnValueReference()), r, on_error)
            self.emit_return(on_error, chain)
            return Chain()
        elif isinstance(node, Raise):
            if node.value is None:
                found = False
                # Walk over the block stack ("outwards") to find the exception block this re-raise is contained in.
                for scope in self._scopes:
                    if isinstance(scope, ExceptionScope):
                        chain.append_update(ExceptionReference(), terms.Read(scope.exception_reference), on_error=on_error)
                        found = True
                if not found:
                    raise AssertionError(
                        "A raise statement without an expression should not occur outside a try block!")
            else:
                e, chain = self.translate_expression(chain, node.value, dec, on_error)
                chain.append_update(ExceptionReference(), e, on_error)
            chain.append_jump(on_error)
            return Chain()
        elif isinstance(node, Break):
            return self.emit_break(on_error, chain)
        elif isinstance(node, Continue):
            return self.emit_continue(on_error, chain)
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
            head = Chain()
            body = Chain()
            successor = Chain()
            chain.append_jump(head)
            condition, head = self.translate_expression(head, node.condition, dec, on_error)
            head.append_guard({condition: body, negate(condition): successor}, on_error)
            self._scopes.push(LoopScope(self._scopes.top, head, successor))
            body = self.translate_statement(body, node.body, dec, on_error)
            self._scopes.pop()
            body.append_jump(head)
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

            stopper = Chain()
            body = Chain()
            successor = Chain()

            iterable, chain = self.translate_expression(chain, node.iterable, dec, on_error)
            callee, chain = self.translate_expression(chain, Attribute(iterable, "__iter__"), dec, on_error)
            iterator, chain = self.emit_call(chain, callee, [], on_error)

            self.declare_pattern(chain, node.pattern, on_error)

            chain.append_jump(body)

            callee, body = self.translate_expression(body, Attribute(iterator, "__next__"), dec, on_error)
            element, body = self.emit_call(body, callee, [], stopper)

            s = terms.IsInstance(terms.Read(ExceptionReference()), TStopIteration.instance)
            stopper.append_guard({s: successor, ~s: on_error}, on_error)
            successor.append_update(ExceptionReference(), terms.CNone(), on_error)

            t, head = self.translate_expression(chain, element, dec, on_error)
            _, head = self.emit_assignment(head, node.pattern, dec, t, on_error)

            self._scopes.push(LoopScope(self._scopes.top, head, successor))
            self.translate_statement(body, node.body, dec, on_error)
            self._scopes.pop()
            body.append_jump(body)
            return successor
        elif isinstance(node, Try):

            body = Chain()
            handler = Chain()
            restoration = Chain()
            finally_head = Chain()
            successor = Chain()
            exception = self.declare_pattern(body, None, on_error)
            self._scopes.push(ExceptionScope(self._scopes.top, exception, finally_head))
            self.translate_statement(body, node.body, dec, handler)
            body.append_jump(finally_head)

            # As the very first step, the exception variable of the task is cleared:
            handler.append_update(exception, terms.Read(ExceptionReference()), on_error)
            handler.append_update(ExceptionReference(), terms.CNone(), on_error)

            for h in node.handlers:
                sc = Chain()
                hc = Chain()
                handler, t = self.translate_expression(handler, h.type, dec, finally_head)
                match = terms.IsInstance(exception, t)
                handler.append_guard({match: hc, ~match: sc}, finally_head)

                # FIXME: The following line looks so nonsensical that I did not even bother to adjust it to the
                #        fact that _decl2ref was factored out into ScopeStack...
                self._decl2ref[h] = exception
                hc = self.translate_statement(hc, h.body, dec, finally_head)
                hc.append_jump(finally_head)

                handler = sc

            # If none of the handlers apply, restore the exception variable and jump to the finally:
            handler.append_jump(restoration)

            restoration.append_update(ExceptionReference(), terms.Read(exception), on_error)
            restoration.append_update(exception, terms.CNone(), on_error)
            restoration.append_jump(finally_head)

            self._scopes.pop()

            if node.final is not None:
                # The finally clause first stashes the current exception and return value away:
                returnvalue = self.declare_pattern(finally_head, None, on_error)
                finally_head.append_update(exception, terms.Read(ExceptionReference()), on_error)
                finally_head.append_update(ExceptionReference(), terms.CNone(), on_error)
                finally_head.append_update(returnvalue, terms.Read(ReturnValueReference()), on_error)
                finally_head.append_update(ReturnValueReference(), terms.CNone(), on_error)
                # Then it executes its body:
                finally_foot = self.translate_statement(finally_head, node.final, dec, on_error)
                # Then it restores the stashed exception and return value:
                finally_foot.append_update(ReturnValueReference(), terms.Read(returnvalue), on_error)
                finally_foot.append_update(ExceptionReference(), terms.Read(exception), on_error)
                finally_foot.append_update(returnvalue, terms.CNone(), on_error)
            else:
                finally_foot = finally_head

            # Then it decides where to jump to, depending on the exception that caused the finally to be entered:
            e = terms.Read(ExceptionReference())
            condition_return = terms.IsInstance(e, types.TReturnException())
            condition_break = terms.IsInstance(e, types.TBreakException())
            condition_continue = terms.IsInstance(e, types.TContinueException())

            condition_exception = terms.IsInstance(e, types.TException()) & ~condition_break & ~condition_continue & ~condition_return
            condition_termination = terms.Comparison(ComparisonOperator.IS, e, terms.CNone)
            finally_foot.append_guard({condition_termination: successor,
                                       condition_return: self.emit_return(on_error),
                                       condition_break: self.emit_break(on_error),
                                       condition_continue: self.emit_continue(on_error),
                                       condition_exception: on_error,
                                       }, on_error)

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

            getter, chain = self._emit_procedure(chain, None, ["self"], node.getter, dec, on_error)
            setter, chain = self._emit_procedure(chain, None, ["self", node.vname], node.setter, dec, on_error)

            # A property is a special kind of descriptor (see https://docs.python.org/3/glossary.html#term-descriptor).
            # A property object does not have private data. It only holds the getter and the setter. Both those
            # methods take an instance as argument and then read/write that.

            name = self.declare_pattern(chain, node.name, on_error)
            chain = chain.append_update(name, terms.NewProperty(getter, setter), on_error)
            return name, chain

        elif isinstance(node, ClassDefinition):
            self._scopes.push(ClassScope(self._scopes.top))

            name = self.declare_pattern(chain, node.name, on_error)

            super_classes = []
            for s_expression in node.bases:
                s_term = self.translate_expression(chain, s_expression, dec, on_error)
                super_classes.append(s_term)

            # We create a new Namespace object and put it into the stack frame.
            chain = chain.append_push()
            chain = chain.append_update(FrameReference(0), terms.NewNamespace(), exit)

            chain = self.translate_statement(chain, node.body, dec, on_error)

            chain = chain.append_update(name, terms.NewClass(super_classes, terms.Read(FrameReference(0))), on_error)
            chain = chain.append_pop()

            self._scopes.pop()

            return chain

        elif isinstance(node, (ImportNames, ImportSource)):

            ms = check_type(dec[node.source], ModuleSpecification)
            subnames = list(map(str, node.source.identifiers[1:]))

            if isinstance(node, ImportSource):
                mapping = {}
                if node.alias is None:
                    if not (len(node.source.Identifiers) == 1):
                        raise NotImplementedError("Code generation for a source import that contains dots has not been implemented!")
                    name = node.source.Identifiers[0]
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

        d = self.declare_pattern(preamble, None, panic)
        d = AbsoluteFrameReference(0, 0, d.index)
        preamble.append_update(TRef(d), NewDict(), panic)

        self._scopes.push(FunctionScope(self._scopes.top))
        imp_code = Chain()
        load1 = Chain()
        load2 = Chain()
        exit = Chain()
        l = self.declare_pattern(imp_code, None, panic)
        imp_code.append_push(CTerm(VDict.get), [Read(TRef(d)), Read(TRef(l))], load1)
        imp_code.append_pop()
        load1.append_update(TRef(ExceptionReference()), CNone(), panic)
        load1.append_push(Read(TRef(l)), [], exit)
        error = terms.Comparison(ComparisonOperator.NEQ, terms.Read(TRef(ExceptionReference())), terms.CNone())
        load1.append_guard({error: exit, negate(error): load2}, panic)
        h = self.declare_pattern(load2, None, panic)
        load2.append_update(TRef(h), Read(TRef(ReturnValueReference())), panic)
        load2.append_push(CTerm(VDict.set), [Read(TRef(d)), Read(TRef(l)), Read(TRef(ReturnValueReference()))], panic)
        load2.append_update(TRef(ReturnValueReference()), Read(TRef(h)), panic)
        load2.append_jump(exit)
        exit.append_pop()
        self._scopes.pop()

        d = AbsoluteFrameReference(0, 0, 1)
        preamble.append_update(TRef(d), CTerm(VProcedure(1, ProgramLocation(imp_code.compile(), 0))), panic)

        return preamble

    def translate_module(self, nodes, dec):
        """
        Generates code for an entire module.
        :param nodes: An iterable of statements that represent the code of the module.
        :param dec: A dict mapping AST nodes to decorations.
        :return: A Chain object.
        """

        # We assume that somebody put a fresh frame on the stack.

        a = VariableAnalysis(Block(nodes), dec)
        self._cells = set(v for v in a.variables if not a.safe_on_stack(v))

        block = Chain()
        entry = block
        exit = Chain()

        # We create a new Namespace object and put it into the stack frame.
        block.append_update(TRef(FrameReference(0)), terms.NewNamespace(), exit)

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
        block.append_update(TRef(ReturnValueReference()), terms.Read(TRef(FrameReference(0))), exit)

        block.append_pop()
        exit.append_pop()

        self._scopes.pop()

        return entry

    def translate(self, spec):
        """
        Translate a standalone program.
        :param spec: A ModuleSpecification to translate into a standalone program.
        :return: A Chain object.
        """
        self._scopes.push(ModuleScope())
        code = self.emit_preamble()
        on_error = Chain()
        on_error.append_pop()
        self.emit_import(code, spec, [],  None,{}, on_error)
        self._scopes.pop()
        return code