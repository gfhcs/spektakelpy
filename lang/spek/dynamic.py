from lang.translator import Translator
from .ast import Pass, Constant, Identifier, Attribute, Tuple, Projection, Call, Launch, Await, Comparison, \
    BooleanBinaryOperation, UnaryOperation, ArithmeticBinaryOperation, ImportNames, ImportSource, \
    ExpressionStatement, Assignment, Block, Return, Raise, Break, \
    Continue, Conditional, While, For, Try, VariableDeclaration, ProcedureDefinition, \
    PropertyDefinition, ClassDefinition
from engine.tasks.instructions import Push, Pop, Launch, Update, Guard, StackProgram
from engine.tasks.reference import ReturnValueReference, ExceptionReference

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
        self.append_guard({Truth(): target}, None)

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

    def translate_expression(self, chain, node, dec, on_error):
        """
        Translates an AST expression into a machine expression.
        :param node: An AST node representing an expression.
        :param dec: A dict mapping AST nodes to decorations.
        :return: A machine Expression object.
        """

        # TODO: For those expressions that can be interrupted by other tasks, i.e. for Call and Await
        # building an expression object.

        if isinstance(node, Constant):

            # TODO: Return a Term object that represents the constant.

        elif isinstance(node, Identifier):

            # TODO: Here we have to use dec to look up the declaration for the *node* (not the name!).
            #       Some member of the Translator must map *declarations* (i.e. AST nodes) to Term objects that represent
            #       the declared variable.

        elif isinstance(node, Attribute):

            # TODO: The code we generate here must do the following:
            #       1. Evaluate the value.
            #       2. Get its type object of the value.
            #       3. Ask the type object for the identifier.

            # Probably we will need some special kind of machine instructions/term that can deal with type objects.

        elif isinstance(node, Call):

            # TODO: This must generate a push instruction. But also we must check if the callee is in fact callable!

        elif isinstance(node, Launch):

            # TODO: We must generate a launch instruction here. Otherwise there are similar problems as for Call.

        elif isinstance(node, Await):

            # TODO: This must generate a guard instruction with only one alternative. The condition is that
            #       the task we are waiting for (obtained by evaluating the given expression, represented by a TID)
            #       completely clears its stack.
            #       After this guard instruction, we need to check the return and exception variables of the task,
            #       to determine whether we can just pass on the return value or whether an exception occured in the
            #       task.

        elif isinstance(node, (Tuple, Projection,
                               Comparison, BooleanBinaryOperation, UnaryOperation, ArithmeticBinaryOperation)):

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
        elif isinstance(node, (ImportNames, ImportSource)):

            # TODO: These things should basically call procedures that execute the imported modules, building Module
            #       values. To match Python's behavior, the procedure building a module must be executed at most once,
            #       i.e. repeated imports of the same module must use a cache!
            #       Other than that, Python's behavior can be matched if we simply declare the import aliases
            #       as local variables and assign the corresponding module members to them.

        elif isinstance(node, ExpressionStatement):
            _ = self.translate_expression(chain, node.expression, dec, on_error)
            # The previous line generated code for any side effects of the expression.
            # We do not really need to use the expression itself,
            # because its evaluation result is not to be bound to anything.
            return chain
        elif isinstance(node, Assignment):
            e = self.translate_expression(chain, node.value, dec, on_error)
            t = self.translate_target(chain, node.target, dec, on_error)
            chain.append_update(t, e, on_error)
            return chain
        elif isinstance(node, Block):
            for s in node:
                chain = self.translate_statement(chain, s, dec, on_error)
            return chain
        elif isinstance(node, Return):
            if node.value is not None:
                r = self.translate_expression(chain, node.value, dec, on_error)
                chain.append_update(ConstantExpression(ReturnValueReference()), r, on_error)
            chain.append_pop()
            return Chain()
        elif isinstance(node, Raise):
            if node.value is not None:
                e = self.translate_expression(chain, node.value, dec, on_error)
                chain.append_update(ConstantExpression(ExceptionReference()), e, on_error)
            chain.append_jump(on_error)
            return Chain()
        elif isinstance(node, (Break, Continue)):
            chain.append_jump(self._loop_successors[-1] if isinstance(node, Break) else self._loop_headers[-1])
            return Chain()
        elif isinstance(node, Conditional):
            consequence = Chain()
            alternative = Chain()
            successor = Chain()
            condition = self.translate_expression(chain, node.condition, dec, on_error)
            chain.append_guard({condition: consequence, ~condition: alternative}, on_error)
            self.translate_statement(consequence, node.consequence, dec, on_error)
            consequence.append_jump(successor)
            self.translate_statement(alternative, node.consequence, dec, on_error)
            alternative.append_jump(successor)
            return successor
        elif isinstance(node, While):
            head = Chain()
            body = Chain()
            successor = Chain()
            chain.append_jump(head)
            condition = self.translate_expression(head, node.condition, dec, on_error)
            head.append_guard({condition: body, ~condition: successor}, on_error)
            self._loop_headers.append(head)
            self._loop_successors.append(successor)
            self.translate_statement(body, node.body, dec, on_error)
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
                        x = it.__next__()
                    except StopIteration:
                        break
                    <body>
            """

            head = Chain()
            stopper = Chain()
            body = Chain()
            successor = Chain()

            iterable = self.translate_expression(chain, node.iterable, dec, on_error)
            iterator = self.emit_call(chain, terms.Member(iterable, "__iter__"), [], on_error)

            chain.append_jump(head)

            element = self.emit_call(head, terms.Member(iterator, "__next__"), [], stopper)

            # TODO: Define stopper: Should jump to successor on StopIteration, but go to on_error otherwise.

            head.append_jump(body)

            self._loop_headers.append(head)
            self._loop_successors.append(successor)
            # TODO: Here we need to bind the term 'element' to the pattern the iteration element is assigned to!
            self.translate_statement(body, node.body, dec, on_error)
            self._loop_headers.pop()
            self._loop_successors.pop()
            body.append_jump(head)
            return successor
        elif isinstance(node, Try):

            # TODO: Any errors occuring in the body must lead to a jump into a general handler. This general handler
            # must further distinguish between the different kinds of error.

        elif isinstance(node, VariableDeclaration):

            # TODO: This thing should just ask for some new variable to be created, via self.create_local()
            #       Such declarations are collected and will eventually be recorded as a property of the function
            #       such that whenever this function is called, the stack frame can be allocated properly.

        elif isinstance(node, ProcedureDefinition):

            # TODO: Here, some Function object must be built, i.e. we need to translate the body of the function and
            #       record its signature and stack frame layout. We then simply declare the name of the function as
            #       a variable (see VariableDeclaration) and assign the function object to that variable.

        elif isinstance(node, PropertyDefinition):

            # TODO: Note that these things work like procedures basically, but should probably be turned into "special"
            #       procedure objects, such that they can be treated properly when assigning to properties or reading
            #       from properties.

        elif isinstance(node, ClassDefinition):

            # TODO: Similar as with a Procedure definition we need to construct a type object here, declare the name
            #       of the type as a variable and then assign the type object to that variable.

        else:
            raise NotImplementedError()


    def translate(self, node, dec):
        pass

