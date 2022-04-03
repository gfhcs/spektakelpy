from engine.tasks import terms
from engine.tasks.instructions import Push, Pop, Launch, Update, Guard, StackProgram
from engine.tasks.reference import ReturnValueReference, ExceptionReference
from lang.translator import Translator
from .ast import Pass, Constant, Identifier, Attribute, Tuple, Projection, Call, Launch, Await, Comparison, \
    BooleanBinaryOperation, BooleanBinaryOperator, UnaryOperation, ArithmeticBinaryOperation, ImportNames, ImportSource, \
    ExpressionStatement, Assignment, Block, Return, Raise, Break, \
    Continue, Conditional, While, For, Try, VariableDeclaration, ProcedureDefinition, \
    PropertyDefinition, ClassDefinition


class Chain:
    """
    Represents a sequence of instructions. Control flow can enter this chain only at its start.
    """
    def __init__(self):
        self._proto = []
        self._targets = set()
        self._can_continue = True

    def _assert_continuable(self):
        if self._proto is None:
            raise RuntimeError("This chain has been finalized and cannot be modified anymore!")
        if not self._can_continue:
            raise RuntimeError("This chain cannot be extended, because of the type of its last instruction!")

    def append_update(self, ref, expression, on_error):
        """
        Appends a prototype of an update instruction to this chain.
        :param ref: An Expression specifying which part of the state is to be updated.
        :param expression: The Expression object specifying how to compute the new value.
        :param on_error: The chain to jump to if the instruction causes an error.
        """
        self._assert_continuable()
        self._proto.append((Update, ref, expression, on_error))
        self._targets.add(on_error)

    def append_guard(self, alternatives, on_error):
        """
        Appends a prototype of a guard instruction to this chain. The chain cannot be continued after a guard
        instruction.
        :param alternatives: A mapping from Expressions to Chains, specifying to which chain to jump under which
                             condition.
        :param on_error: The chain to jump to in case the instruction causes an error.
        """
        self._assert_continuable()
        self._proto.append((Guard, alternatives, on_error))
        for _, t in alternatives.items():
            self._targets.add(t)
        self._targets.add(on_error)
        self._can_continue = False

    def append_jump(self, target):
        """
        Appends a prototype of an unconditional jump instruction to this chain. The chain cannot be continued after this.
        :param target: The chain to jump to.
        """
        # According to the semantics, there cannot be an error in evaluating Truth():
        self.append_guard({terms.Truth(): target}, None)

    def append_push(self, entry, aexpressions, on_error):
        """
        Appends a prototype of a Push instruction to this chain.
        :param entry: An Expression that evaluates to a ProgramLocation.
        :param aexpressions: An iterable of Expression objects that determine the values for the local variables that
                            are to be pushed as part of the stack frame.
        :param on_error: The chain to jump to in case the instruction causes an error.
                         Note that any errors caused as long as the newly pushed stack frame still exists will _not_
                         lead to this error destination! To handle those errors, instructions following the push
                         instruction must explicitly treat them!
        """
        self._assert_continuable()
        self._proto.append((Push, entry, aexpressions, on_error))
        self._targets.add(on_error)

    def append_pop(self):
        """
        Appends a prototype of a Pop instruction to this chain.
        The chain cannot be continued after a pop instruction.
        """
        self._assert_continuable()
        self._proto.append((Pop, ))
        self._can_continue = False

    def append_launch(self, entry, aexpressions, on_error):
        """
        Appends a prototype of a Launch instruction to this chain.
        :param entry: An Expression that evaluates to a ProgramLocation.
        :param aexpressions: An iterable of Expression objects that determine the values for the local variables that
                            are to be pushed as part of the stack frame.
        :param on_error: The chain to jump to in case the instruction causes an error.
                         Note that any errors caused as long as the newly pushed stack frame still exists will _not_
                         lead to this error destination! To handle those errors, instructions following the push
                         instruction must explicitly treat them!
        """
        self._assert_continuable()
        self._proto.append((Launch, entry, aexpressions, on_error))
        self._targets.add(on_error)

    def compile(self):
        """
        Compiles this chain and the chains it may jump to into a StackProgram.
        :return: A StackProgram object.
        """

        offset = 0
        entries = {}
        chains = [self]

        while len(chains) > 0:
            c = chains.pop()
            if c in entries:
                continue
            if c._can_continue:
                raise RuntimeError("Cannot compile chains that do not end with either a guard or a pop instruction!")
            entries[c] = offset
            offset += len(c)
            chains.extend(c._targets)

        instructions = []
        offset = 0

        for c in entries.keys(): # Enumerates the chains in the order they were inserted, guaranteeing that they start
                                 # exactly at the recorded offsets.
            for t, *args in c._proto:
                if t is Update:
                    ref, expression, on_error = args
                    instructions.append(Update(ref, expression, offset + 1, entries[on_error]))
                elif t is Guard:
                    alternatives, on_error = args
                    instructions.append(Guard({condition: entries[chain] for condition, chain in alternatives.items()}, entries[on_error]))
                elif t is Push:
                    entry, expressions, on_error = args
                    instructions.append(Push(entry, expressions, offset + 1, entries[on_error]))
                elif t is Pop:
                    instructions.append(Pop())
                elif t is Launch:
                    entry, expressions, on_error = args
                    instructions.append(Launch(entry, expressions, offset + 1, entries[on_error]))
                else:
                    raise NotImplementedError("Bug in Chain.compile: The instruction type {} "
                                              "has not been taken into account for compilation yet!".format(t))
                offset += 1

        return StackProgram(instructions)

class Spektakel2Stack(Translator):
    """
    A translator that translates Spektakel AST nodes into stack programs.
    """

    def __init__(self):
        super().__init__()
        self._decl2ref = {} # Maps declaration nodes to references.
        self._loop_headers = [] # Stack of loop entry points.
        self._loop_successors = [] # Stack of loop successor blocks.

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
        chain.append_push(callee, args, on_error)

        successor = Chain()
        noerror = terms.Equal(terms.Read(ExceptionReference()), terms.CNone())
        chain.append_guard({~noerror: on_error, noerror: successor}, on_error)

        rv = self.get_local()
        rr = ReturnValueReference()
        successor.append_update(rv, terms.Read(rr), on_error)
        return rv, successor

    # noinspection PyRedundantParentheses
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
                return (terms.CTrue() if value == True else terms.CFalse()), chain
            elif isinstance(value, str):
                return (terms.String(value), chain)
            elif value is None:
                return (terms.CNone(), chain)
            elif isinstance(value, int):
                return (terms.Int(value), chain)
            elif isinstance(value, float):
                return (terms.Float(value), chain)
            else:
                raise NotImplementedError("Translation of constant expressions of type {}"
                                          " has not been implemented!".format(type(value)))
        elif isinstance(node, Identifier):
            return (self._decl2term[dec[node]], chain)
        elif isinstance(node, Attribute):
            v, chain = self.translate_expression(chain, node.value, dec, on_error)
            return terms.Lookup(v, node.name), chain
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
            tid = self.get_local()
            chain.append_update(tid, terms.Read(ReturnValueReference()), on_error)
            return tid, chain
        elif isinstance(node, Await):
            tid = self.translate_expression(chain, node.process, dec, on_error)
            successor = Chain()
            complete = terms.Terminated(tid)
            chain.append_guard({complete: successor}, on_error)

            successor = Chain()
            noerror = terms.Equal(terms.Read(ExceptionReference()), terms.CNone())
            chain.append_guard({~noerror: on_error, noerror: successor}, on_error)

            rv = self.get_local()
            rr = ReturnValueReference()
            successor.append_update(rv, terms.Read(rr), on_error)
            successor.append_update(rr, terms.CNone(), on_error)
            return rv, successor
        elif isinstance(node, Projection):
            idx, chain = self.translate_expression(chain, node.index, dec, on_error)
            v, chain = self.translate_expression(chain, node.value, dec, on_error)
            return self.emit_call(chain, terms.Lookup(v, "__getitem__"), [idx], on_error)
        elif isinstance(node, UnaryOperation):
            return terms.UnaryOperation(node.operator, self.translate_expression(chain, node.operand, dec, on_error)), chain
        elif isinstance(node, ArithmeticBinaryOperation):
            return terms.ArithmeticBinaryOperation(node.operator,
                                                   self.translate_expression(chain, node.left, dec, on_error),
                                                   self.translate_expression(chain, node.right, dec, on_error)), chain
        elif isinstance(node, Comparison):
            return terms.Comparison(node.operator,
                                    self.translate_expression(chain, node.left, dec, on_error),
                                    self.translate_expression(chain, node.right, dec, on_error)), chain
        elif isinstance(node, BooleanBinaryOperation):
            # Note: Like in Python, we want AND and OR to be short-circuited. This means that we require some control
            #       flow in order to possibly skip the evaluation of the right operand.

            v = self.get_local()
            left, chain = self.translate_expression(chain, node.left, dec, on_error)
            chain.append_update(v, left, on_error)

            rest = Chain()
            successor = Chain()

            if node.operator == BooleanBinaryOperator.AND:
                skip = ~terms.Read(v)
            elif node.operator == BooleanBinaryOperator.OR:
                skip = terms.Read(v)
            else:
                skip = terms.CFalse()

            chain.append_guard({skip: successor, ~skip: rest})

            right, rest = self.translate_expression(rest, node.right, dec, on_error)
            chain.append_update(v, terms.BooleanBinaryOperation(node.operator, terms.Read(v), right), on_error)
            chain.append_jump(successor)
            return terms.Read(v), successor
        elif isinstance(node, Tuple):
            return terms.Tuple(*(self.translate_expression(chain, c, dec, on_error) for c in node.children)), chain
        else:
            raise NotImplementedError()

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
            pass
        elif isinstance(node, ExpressionStatement):
            _, chain = self.translate_expression(chain, node.expression, dec, on_error)
            # The previous line generated code for any side effects of the expression.
            # We do not really need to use the expression itself,
            # because its evaluation result is not to be bound to anything.
            return chain
        elif isinstance(node, Assignment):
            e, chain = self.translate_expression(chain, node.value, dec, on_error)
            chain = self.emit_pattern_assignment(chain, node.target, dec, e, on_error)
            return chain
        elif isinstance(node, Block):
            for s in node:
                chain = self.translate_statement(chain, s, dec, on_error)
            return chain
        elif isinstance(node, Return):
            if node.value is not None:
                r, chain = self.translate_expression(chain, node.value, dec, on_error)
                chain.append_update(ReturnValueReference(), r, on_error)
            chain.append_pop()
            return Chain()
        elif isinstance(node, Raise):
            if node.value is not None:
                e, chain = self.translate_expression(chain, node.value, dec, on_error)
                chain.append_update(ExceptionReference(), e, on_error)
            chain.append_jump(on_error)
            return Chain()
        elif isinstance(node, (Break, Continue)):
            chain.append_jump(self._loop_successors[-1] if isinstance(node, Break) else self._loop_headers[-1])
            return Chain()
        elif isinstance(node, Conditional):
            consequence = Chain()
            alternative = Chain()
            successor = Chain()
            condition, chain = self.translate_expression(chain, node.condition, dec, on_error)
            chain.append_guard({condition: consequence, ~condition: alternative}, on_error)
            consequence = self.translate_statement(consequence, node.consequence, dec, on_error)
            consequence.append_jump(successor)
            alternative = self.translate_statement(alternative, node.consequence, dec, on_error)
            alternative.append_jump(successor)
            return successor
        elif isinstance(node, While):
            head = Chain()
            body = Chain()
            successor = Chain()
            chain.append_jump(head)
            condition, head = self.translate_expression(head, node.condition, dec, on_error)
            head.append_guard({condition: body, ~condition: successor}, on_error)
            self._loop_headers.append(head)
            self._loop_successors.append(successor)
            body = self.translate_statement(body, node.body, dec, on_error)
            self._loop_headers.pop()
            self._loop_successors.pop()
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
            iterator, chain = self.emit_call(chain, terms.Member(iterable, "__iter__"), [], on_error)

            self.declare_pattern(node.pattern)

            chain.append_jump(body)

            element, body = self.emit_call(body, terms.Member(iterator, "__next__"), [], stopper)

            s = terms.IsInstance(terms.Read(ExceptionReference()), types.builtin.StopIteration)
            stopper.append_guard({s: successor, ~s: on_error}, on_error)
            successor.append_update(ExceptionReference(), terms.CNone(), on_error)

            head = self.emit_pattern_assignment(chain, node.pattern, dec, element, on_error)

            self._loop_headers.append(head)
            self._loop_successors.append(successor)
            self.translate_statement(body, node.body, dec, on_error)
            self._loop_headers.pop()
            self._loop_successors.pop()
            body.append_jump(body)
            return successor
        elif isinstance(node, Try):

            body = Chain()
            handler = Chain()
            successor = Chain()
            self.translate_statement(body, node.body, dec, handler)
            body.append_jump(successor)

            # TODO: There are the following cases for the execution of the body:
            # Jump (break, continue, return)
            # Exception
            # Normal termination
            # In all those cases, the finally clause is executed as the final part of the statement.
            # However, the *latest* exception occuring before the finally is saved and then re-raised, *if* the finally
            # terminates normally.


            # TODO: When an exception is raised, it sits in the ExceptionReference() slots. We must clear this
            # slot before any other procedures are called, because the exception will otherwise be interepreted as
            # coming from those later calls!

            halternatives = {}

            for h in node.handlers:
                c = Chain()

                # TODO: We must have the condition "None of the previous handlers fired, while the exception does have the right type for this handler"
                self.translate_expression(chain, terms.IsInstance(...))

                # TODO: At this point we need to allocate memory for the exception variable!
                self.translate_statement(c, h.body, dec, on_error)
                c.append_jump(successor)

                halternatives[condition] = c

            handler.append_guard(halternatives, on_error)

            return successor
        elif isinstance(node, VariableDeclaration):
            self.declare_pattern(node.pattern)
            if node.expression is not None:
                chain = self.emit_pattern_assignment(chain, node.pattern, dec, node.expression)
            return chain
        elif isinstance(node, ProcedureDefinition):

            # TODO: Here, some Function object must be built, i.e. we need to translate the body of the function and
            #       record its signature and stack frame layout. We then simply declare the name of the function as
            #       a variable (see VariableDeclaration) and assign the function object to that variable.

            # TODO: This thing must, after the body has been translated, harvest self._decl2term , such that stack
            #       frames of the right size can be allocated at call sites.

        elif isinstance(node, PropertyDefinition):

            # TODO: Note that these things work like procedures basically, but should probably be turned into "special"
            #       procedure objects, such that they can be treated properly when assigning to properties or reading
            #       from properties.

        elif isinstance(node, ClassDefinition):

            # TODO: Similar as with a Procedure definition we need to construct a type object here, declare the name
            #       of the type as a variable and then assign the type object to that variable.

        elif isinstance(node, (ImportNames, ImportSource)):

            # TODO: These things should basically call procedures that execute the imported modules, building Module
            #       values. To match Python's behavior, the procedure building a module must be executed at most once,
            #       i.e. repeated imports of the same module must use a cache!
            #       Other than that, Python's behavior can be matched if we simply declare the import aliases
            #       as local variables and assign the corresponding module members to them.

        else:
            raise NotImplementedError()


    def translate(self, node, dec):
        pass

