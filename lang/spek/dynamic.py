from engine.tasks import terms
from engine.tasks.instructions import Push, Pop, Launch, Update, Guard, StackProgram
from engine.tasks.reference import ReturnValueReference, ExceptionReference
from lang.translator import Translator
from .ast import Pass, Constant, Identifier, Attribute, Tuple, Projection, Call, Launch, Await, Comparison, \
    BooleanBinaryOperation, BooleanBinaryOperator, UnaryOperation, ArithmeticBinaryOperation, ImportNames, ImportSource, \
    ExpressionStatement, Assignment, Block, Return, Raise, Break, \
    Continue, Conditional, While, For, Try, VariableDeclaration, ProcedureDefinition, \
    PropertyDefinition, ClassDefinition, Statement, AssignableExpression
from collections import namedtuple


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


class BlockStack:
    """
    Models a stack to which information about syntactic blocks can be pushed during code generation.
    """

    LoopBlock = namedtuple("LoopBlock", ("headChain", "successorChain"))
    ExceptionBlock = namedtuple("ExceptionBlock", ("exceptionReference", "finallyChain"))
    FunctionBlock = namedtuple("FunctionBlock", ("offset", ))
    ClassBlock = namedtuple("ClassBlock", ("offset", ))
    ModuleBlock = namedtuple("ModuleBlock", ("offset", ))

    def __init__(self):
        super().__init__()
        self._entries = []

    def push(self, entry):
        """
        Pushes an entry to the top of the stack.
        :param entry: The entry to push.
        """
        self._entries.append(entry)

    def pop(self):
        """
        Removes the latest entry from the stack.
        :return: The entry that was popped.
        """
        return self._entries.pop()

    @property
    def top(self):
        """
        The entry on the top of the stack.
        """
        return self._entries[-1]

    def __iter__(self):
        return reversed(self._entries)

    def __len__(self):
        return len(self._entries)


class Spektakel2Stack(Translator):
    """
    A translator that translates Spektakel AST nodes into stack programs.
    """

    def __init__(self):
        super().__init__()
        self._decl2ref = {} # Maps declaration nodes to references.
        self._blocks = BlockStack()

    def declare_name(self, chain, node, on_error):
        """
        Statically declares a new variable name. Depending on the context the name will be declared as a stack frame
        variable, or as a namespace entry. The new variable is recorded for the given declaration, such that it can
        easily be retrieved later.
        :param chain: The Chain to which the instructions for allocating the new variable should be appended.
        :param on_error: The Chain to which control should be transferred if the allocation code fails.
        :param node: The AST node for which to create a new variable. It may be None, in which case an anonymous local
                     variable is allocated on the stack.
        :return: A Reference object that represents the newly allocated variable.
        """

        blocks_iter = iter(self._blocks)

        try:
            idx, top = 0, next(blocks_iter)
        except StopIteration:
            raise Exception("Bug in create_local!")

        if node is None:
            name = None
        elif isinstance(node, Identifier):
            name = node.name
        elif isinstance(node, ProcedureDefinition):
            name = node.name
        elif isinstance(node, PropertyDefinition):
            name = node.name
        elif isinstance(node, ClassDefinition):
            name = node.name
        else:
            raise NotImplementedError("Declaring names for AST nodes of type {} has not been implemented yet!".format(type(node)))

        while True:
            if isinstance(top, BlockStack.FunctionBlock) \
                    or (name is None and isinstance(top, (BlockStack.ClassBlock, BlockStack.ModuleBlock))):
                # We are declaring a local variable in the stack frame (either for a function, or in a class/module
                # definition, in which an anonymous variable is needed).
                # The stack frame always has the same layout for all invocations of that function/declaration,
                # so we just add one more variable to that layout.
                offset = top.offset
                self._blocks[idx] = type(top)(offset + 1)
                r = FrameReference(offset)
                self._decl2ref[node] = r
                return r
            elif isinstance(top, (BlockStack.ClassBlock, BlockStack.ModuleBlock)):
                # We are declaring a class/module member. We know that the class/module definition code is
                # running under a stack frame that has a Namespace object at offset 0. That object needs to be extended.
                slot = FrameReference(0)
                chain.append_update(slot, terms.Adjunction(terms.Read(slot), name, terms.CNone), on_error)
                r = NameReference(slot, name)
                self._decl2ref[node] = r
                return r
            else:
                try:
                    idx, top = idx + 1, next(blocks_iter)
                except StopIteration:
                    raise Exception("Bug in create_local!")

    def declare_pattern(self, chain, pattern, on_error):
        """
        Statically declares new variable names for an entire pattern of names.
        Depending on the context the names will be declared as stack frame
        variables, or as a namespace entries. The new variables are recorded for the given pattern, such that they can
        easily be retrieved later.
        :param chain: The Chain to which the instructions for allocating the new variables should be appended.
        :param on_error: The Chain to which control should be transferred if the allocation code fails.
        :param pattern: The AssignableExpression node holding the pattern expression for which to allocate new variables.
        """

        if isinstance(pattern, Identifier):
            self.declare_name(chain, pattern, on_error)
        elif isinstance(pattern, AssignableExpression):
            for c in pattern.children:
                self.declare_pattern(chain, c, on_error)
        else:
            raise TypeError("Patterns to be declared must only contain AssignableExpression nodes,"
                            " not nodes of type {}!".format(type(pattern)))

    def emit_assignment(self, chain, pattern, dec, expression, on_error):
        """
        Emits VM code for a assigning the result of an expression evaluation to a pattern.
        :param chain: The chain to which the assignment should be appended.
        :param pattern: An AssignableExpression to which a value should be assigned.
        :param dec: A dict mapping AST nodes to decorations.
        :param expression: The expression the result of which is to be assigned.
        :param on_error: The chain that execution should jump to in case of an error.
        :return: The chain with which execution is to be continued after the call.
        """

        # First we evaluate the expression:
        t, chain = self.translate_expression(chain, expression, dec, on_error)

        def assign(chain, pattern, t, on_error):
            if isinstance(pattern, Identifier):
                # TODO: There are 2 possible cases here: Either the identifier refers to a StackReference, in which case
                #       we should simply issue an update statement for the stack address, or it refers to a Namespace
                #       slot, in which case we adjoin that namespace.
            elif isinstance(pattern, Tuple):
                # TODO: What we are doing here will not work if t represents a general iterable! For that we would
                #       need to call a procedure first that turns it into a list of sorts.
                for idx, c in enumerate(pattern.children):
                    chain = assign(chain, c, terms.Project(t, terms.CInt(idx)), on_error)
            elif isinstance(pattern, Projection):
                # TODO: In this case we need to evaluate the left hand side of the projection expression and then call
                #       the __setitem__ procedure on that value.
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

                # TODO: Evaluate the left hand side. Assume that is neither a type, nor a Super instance.

                # TODO: Get the type of the left hand object. Search the MRO of that type for the name of the attribute.
                # TODO: If the name was found and it is a property, call the setter of the property and be done.
                # TODO: If the object contains the name as an instance variable, set the value of that variable and be done.
                # TODO: If the name was found and it is a method, fail.
                # TODO: If the name was found, it must be a class variable at this point. Set that variable and be done.
                # TODO: Raise an AttributeError.

                # TODO: Implement this for left hand sides that denote Type objects, leaving out the instance-based parts.

                # TODO: Implement this for 'super', see https://docs.python.org/3/howto/descriptor.html#invocation-from-super
                #       and https://www.python.org/download/releases/2.2.3/descrintro/#cooperation
            elif isinstance(pattern, AssignableExpression):
                raise NotImplementedError("Assignment to patterns of type {} "
                                          "has not been implemented yet!".format(type(pattern)))
            else:
                raise TypeError("The pattern to which a value is assigned must be an "
                                "AssignableExpression, not a {}!".format(type(pattern)))

        return assign(chain, pattern, t, on_error)

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
        argc_error.append_update(ExceptionReference(), terms.CTypeError("Wrong number of arguments for call!"))
        argc_error.append_jump(on_error)
        match = terms.Equal(terms.NumArgs(callee), terms.CInt(len(args)))
        chain.append_guard({match: call, ~match : argc_error})

        call.append_push(callee, args, on_error)

        successor = Chain()
        noerror = terms.Equal(terms.Read(ExceptionReference()), terms.CNone())
        chain.append_guard({~noerror: on_error, noerror: successor}, on_error)

        rv = self.declare_name(successor, None, on_error)
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
            tid = self.declare_name(chain, None, on_error)
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

            rv = self.declare_name(successor, None, on_error)
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

            v = self.declare_name(chain, None, on_error)
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
        for entry in self._blocks:
            if isinstance(entry, BlockStack.ExceptionBlock):
                chain.append_update(ExceptionReference(), terms.ReturnException(), on_error=on_error)
                chain.append_jump(entry.finallyChain)
                return chain
            elif isinstance(entry, BlockStack.FunctionBlock):
                break

        # We made it to the function level without hitting an exception block.
        chain.append_update(ExceptionReference(), terms.CNone(), on_error=on_error)
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
        for entry in self._blocks:
            if isinstance(entry, BlockStack.ExceptionBlock):
                chain.append_update(ExceptionReference(), terms.BreakException(), on_error=on_error)
                chain.append_jump(entry.finallyChain)
                return chain
            elif isinstance(entry, BlockStack.LoopBlock):
                chain.append_update(ExceptionReference(), terms.CNone(), on_error=on_error)
                chain.append_jump(entry.successorChain)
                return chain

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
        for entry in self._blocks:
            if isinstance(entry, BlockStack.ExceptionBlock):
                chain.append_update(ExceptionReference(), terms.ContinueException(), on_error=on_error)
                chain.append_jump(entry.finallyChain)
                return chain
            elif isinstance(entry, BlockStack.LoopBlock):
                chain.append_update(ExceptionReference(), terms.CNone(), on_error=on_error)
                chain.append_jump(entry.headChain)
                return chain

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

        bodyBlock = Chain()
        exitBlock = Chain()

        num_args = len(argnames)

        self._blocks.push(BlockStack.FunctionBlock(0))

        # Declare the function arguments as local variables:
        for aname in argnames:
            self.declare_pattern(bodyBlock, aname, on_error)

        body = self.translate_statement(bodyBlock, body, dec, exitBlock)
        body.append_pop()

        exitBlock.append_pop()

        # TODO (later): The function definition might be nested in another one.
        #               Since it might "escape" the enclosing function, the variables that are shared between
        #               the function cannot be allocated on the stack.
        #               Those variables that are shared must be allocated in a "Heap frame", the pointer to which
        #               is part of the Function object that is constructed (IT CANNOT BE PASSED AS AN ARGUMENT!
        #               REASON: The function object is not being called here, but later,
        #               by some other code that receives the function object!)
        #               The compilation of the inner function
        #               must thus map the shared variables to offsets in the heap frame.
        #               --> For now we should just *detect* nonlocal variables and raise a NotImplementedError

        f = terms.Function(num_args, body.compile())

        self._blocks.pop()

        if name is None:
            return f, chain
        else:
            name = self.declare_pattern(chain, name, on_error)
            chain = chain.append_update(name, f, on_error)
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
            pass
        elif isinstance(node, ExpressionStatement):
            _, chain = self.translate_expression(chain, node.expression, dec, on_error)
            # The previous line generated code for any side effects of the expression.
            # We do not really need to use the expression itself,
            # because its evaluation result is not to be bound to anything.
            return chain
        elif isinstance(node, Assignment):
            e, chain = self.translate_expression(chain, node.value, dec, on_error)
            chain = self.emit_assignment(chain, node.target, dec, e, on_error)
            return chain
        elif isinstance(node, Block):
            for s in node:
                chain = self.translate_statement(chain, s, dec, on_error)
            return chain
        elif isinstance(node, Return):
            if node.value is not None:
                r, chain = self.translate_expression(chain, node.value, dec, on_error)
                chain.append_update(ReturnValueReference(), r, on_error)
            self.emit_return(on_error, chain)
            return Chain()
        elif isinstance(node, Raise):
            if node.value is None:
                found = False
                # Walk over the block stack ("outwards") to find the exception block this re-raise is contained in.
                for entry in self._blocks:
                    if isinstance(entry, BlockStack.ExceptionBlock):
                        chain.append_update(ExceptionReference(), terms.Read(entry.exceptionVariable), on_error=on_error)
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
            self._blocks.push(BlockStack.LoopBlock(head, successor))
            body = self.translate_statement(body, node.body, dec, on_error)
            self._blocks.pop()
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

            self.declare_pattern(chain, node.pattern, on_error)

            chain.append_jump(body)

            element, body = self.emit_call(body, terms.Member(iterator, "__next__"), [], stopper)

            s = terms.IsInstance(terms.Read(ExceptionReference()), types.builtin.StopIteration)
            stopper.append_guard({s: successor, ~s: on_error}, on_error)
            successor.append_update(ExceptionReference(), terms.CNone(), on_error)

            head = self.emit_assignment(chain, node.pattern, dec, element, on_error)

            self._blocks.push(BlockStack.LoopBlock(head, successor))
            self.translate_statement(body, node.body, dec, on_error)
            self._blocks.pop()
            body.append_jump(body)
            return successor
        elif isinstance(node, Try):

            body = Chain()
            handler = Chain()
            restoration = Chain()
            finally_head = Chain()
            successor = Chain()
            exception = self.declare_name(body, None, on_error)
            self._blocks.push(BlockStack.ExceptionBlock(exception, finally_head))
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

                self._decl2ref[h] = exception
                hc = self.translate_statement(hc, h.body, dec, finally_head)
                hc.append_jump(finally_head)

                handler = sc

            # If none of the handlers apply, restore the exception variable and jump to the finally:
            handler.append_jump(restoration)

            restoration.append_update(ExceptionReference(), terms.Read(exception), on_error)
            restoration.append_update(exception, terms.CNone(), on_error)
            restoration.append_jump(finally_head)

            self._blocks.pop()

            if node.final is not None:
                # The finally clause first stashes the current exception and return value away:
                returnvalue = self.declare_name(finally_head, None, on_error)
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
            condition_return = terms.IsInstance(e, types.ReturnException())
            condition_break = terms.IsInstance(e, types.BreakException())
            condition_continue = terms.IsInstance(e, types.ContinueException())

            condition_exception = terms.IsInstance(e, types.Exception()) & ~condition_break & ~condition_continue & ~condition_return
            condition_termination = terms.Is(e, terms.CNone)
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
                chain = self.emit_assignment(chain, node.pattern, dec, node.expression)
            return chain
        elif isinstance(node, ProcedureDefinition):
            if not isinstance(self._blocks[-1], (BlockStack.ClassBlock, BlockStack.ModuleBlock)):
                raise NotImplementedError("Code generation for procedure definitions on levels other than module level "
                                          "or class level has not been implemented yet!")

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
            if not isinstance(self._blocks[-1], BlockStack.ModuleBlock):
                # This would be probelamtic, because the type might incorporate local variables from the current function
                # stack. This is difficult to implement for the same reason that nested function declarations are.
                raise NotImplementedError("Code generation for class definitions on levels other than module level "
                                          "has not been implemented yet!")

            self._blocks.push(BlockStack.ClassBlock(0))

            name = self.declare_pattern(chain, node.name, on_error)

            super_classes = []
            for s_expression in node.bases:
                s_term = self.translate_expression(chain, s_expression, dec, on_error)
                super_classes.append(s_term)

            # We create a new Namespace object and put it into the stack frame.
            chain = chain.append_push()
            chain = chain.append_update(StackFrameReference(0), terms.NewNamespace(), exit)

            chain = self.translate_statement(chain, node.body, dec, on_error)

            chain = chain.append_update(name, terms.NewClass(super_classes, terms.Read(StackFrameReference(0))), on_error)
            chain = chain.append_pop()

            self._blocks.pop()

            return chain

        elif isinstance(node, (ImportNames, ImportSource)):

            module = dec[node.source.Identifiers[0]]

            assert isinstance(module, CompiledModule)

            m, chain = self.emit_call(chain, self._import_procedure, [module.entry], on_error)

            for a in node.source.Identifiers[1:]:
                m = terms.Lookup(m, a)

            if isinstance(node, ImportSource):
                if node.alias is None:
                    if not (len(node.source.Identifiers) == 1):
                        raise NotImplementedError("Code generation for a source import that contains dots has not been implemented!")
                    name = self.declare_pattern(chain, node.source.Identifiers[0], on_error)
                    chain.append_update(name, m, on_error)
                else:
                    name = self.declare_pattern(chain, node.alias, on_error)
                    chain.append_update(name, m, on_error)
            elif isinstance(node, ImportNames):
                aliases = []
                if node.wildcard:
                    for name, _ in module:
                        if isinstance(name, str):
                            aliases.append((name, module[name]))
                else:
                    for name, alias in node.aliases.items():
                        aliases.append((alias, module[name]))

                for name, member in aliases:
                    name = self.declare_pattern(chain, name, on_error)
                    chain.append_update(name, member, on_error)
            else:
                raise NotImplementedError("Code generation for nodes of type {}"
                                          " has not been implemented!".format(type(node)))

        else:
            raise NotImplementedError()

    def emit_preamble(self):
        """
        Emits code that is to run once at the beginning of execution.
        :return: A Chain object.
        """

        """ We generate code for this:
            
            def ___load___(location):
                return ___call___(location, [Module()])
               
            var mcv = {}

            def ___import___(location):
                try:
                    return mcv[location]
                except KeyError:
                    m = ___load___(location)
                    mcv[location] = m
                    return m
                    
            del mcv
        """

        # Step 1: Define ___load___

        bodyBlock = Chain()
        exitBlock = Chain()

        self._blocks.push(BlockStack.FunctionBlock(0))
        location = self.declare_name(bodyBlock, None, exitBlock)

        bodyBlock.append_push(location, [], exitBlock)

        successor = Chain()
        noerror = terms.Equal(terms.Read(ExceptionReference()), terms.CNone())
        bodyBlock.append_guard({~noerror: exitBlock, noerror: successor}, exitBlock)

        rv = self.declare_name(successor, None, exitBlock)
        rr = ReturnValueReference()
        successor.append_update(rv, terms.Read(rr), exitBlock)
        successor = self.emit_return(exitBlock, chain=successor)

        successor.append_pop()
        exitBlock.append_pop()

        load = terms.Function(1, bodyBlock.compile())

        self._blocks.pop()

        # Step 2: Allocate 'mcv':

        preamble = Chain()

        # Step 3: Translate the AST for ___import___:

        name_import = Identifier("___import___")
        name_location = Identifier("location")
        name_mcv = Identifier("mcv")
        name_m = Identifier("m")

        b = Return(Projection(name_mcv, name_location))

        h = Block([
            VariableDeclaration(name_m, expression=Call(load, name_location)),
            Assignment(Projection(name_mcv, name_location), name_m),
            Return(name_m)
        ])

        body = Block([Try(b, [h], None)])

        preamble_error = Chain()

        mcv = self.declare_name(preamble, None, preamble_error)
        preamble.append_update(mcv, terms.NewDict(), preamble_error)
        dec = {name_mcv: mcv}

        preamble = self.translate_statement(preamble,
                                            ProcedureDefinition(name_import, [name_location], body),
                                            dec,
                                            preamble_error)

        return preamble

    def translate_module(self, nodes, dec):
        """
        Generates code for an entire module.
        :param nodes: An iterable of statements that represent the code of the module.
        :param dec: A dict mapping AST nodes to decorations.
        :return: A StackProgram object.
        """

        # We assume that somebody put a fresh frame on the stack.

        block = Chain()
        exit = Chain()

        # We create a new Namespace object and put it into the stack frame.
        block.append_update(StackFrameReference(0), terms.NewNamespace(), exit)

        # The code of a module assumes that there is 1 argument on the current stack frame, which is the Namespace object
        # that is to be populated. All allocations of local variables must actually be members of that Namespace object.
        self._blocks.push(BlockStack.ModuleBlock(0))

        # We execute the module code completely, which populates that namespace.
        for node in nodes:
            block = self.translate_statement(block, node, dec, exit)

        # Return a Module object. The preamble will store it somewhere.
        block.append_update(ReturnValueReference(), terms.NewModule(terms.Read(StackFrameReference(0))), exit)

        block.append_pop()
        exit.append_pop()

        self._blocks.pop()

        return block.compile()


    def translate(self, node, dec):
        pass

