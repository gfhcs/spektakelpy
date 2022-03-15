from lang.translator import Translator
from .ast import Pass, Constant, Identifier, Attribute, Tuple, Projection, Call, Launch, Await, Comparison, \
    BooleanBinaryOperation, UnaryOperation, ArithmeticBinaryOperation, ImportNames, ImportSource, \
    ExpressionStatement, Assignment, Block, Return, Raise, Break, \
    Continue, Conditional, While, For, Try, VariableDeclaration, ProcedureDefinition, \
    PropertyDefinition, ClassDefinition
from engine.tasks.instructions import Push, Pop, Launch, Update, Guard, StackProgram


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

    def translate_expression(self, node, dec):
        """
        Translates an AST expression into a machine expression.
        :param node: An AST node representing an expression.
        :param dec: A dict mapping AST nodes to decorations.
        :return: A machine Expression object.
        """

        if isinstance(node, Constant):

        elif isinstance(node, Identifier):

        elif isinstance(node, Attribute):

        elif isinstance(node, (Tuple, Projection, Call, Launch, Await,
                               Comparison, BooleanBinaryOperation, UnaryOperation, ArithmeticBinaryOperation)):

        else:
            raise NotImplementedError()

    def translate_statement(self, node, dec):
        """
        Translates a statement into a StackProgram.
        :param node: An AST node representing a Statement.
        :param dec: A dict mapping AST nodes to decorations.
        :return: A StackProgram.
        """

        if isinstance(node, Pass):
            pass
        elif isinstance(node, (ImportNames, ImportSource)):

        elif isinstance(node, ExpressionStatement):
        elif isinstance(node, Assignment):

        elif isinstance(node, Block):

        elif isinstance(node, Return):

        elif isinstance(node, Raise):

        elif isinstance(node, (Break, Continue)):

        elif isinstance(node, Conditional):

        elif isinstance(node, While):

        elif isinstance(node, For):

        elif isinstance(node, Try):

        elif isinstance(node, VariableDeclaration):

        elif isinstance(node, ProcedureDefinition):

        elif isinstance(node, PropertyDefinition):

        elif isinstance(node, ClassDefinition):

        else:
            raise NotImplementedError()


    def translate(self, node, dec):
        pass

