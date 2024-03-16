from engine.stack.instructionset import Push, Launch, Guard, Update, Pop
from engine.stack.program import StackProgram
from lang.spek.data import terms
from util import check_type
from util.printable import Printable


class Chain(Printable):
    """
    Represents a sequence of instructions. Control flow can enter this chain only at its start.
    """
    def __init__(self):
        super().__init__()
        self._proto = []
        self._targets = set()
        self._can_continue = True

    def __hash__(self):
        return hash(tuple(t for t, *_ in self._proto))

    def _equals(self, other, bijection=None):
        if bijection is None:
            bijection = {}
        if not (self._can_continue == other._can_continue and len(self._proto) == len(other._proto)):
            return False
        try:
            return bijection[id(self)] is other
        except KeyError:
            bijection[id(self)] = other
            for (t1, *args1), (t2, *args2) in zip(self._proto, other._proto):
                if t1 is not t2 or len(args1) != len(args2):
                    return False
                for a1, a2 in zip(args1, args2):
                    if isinstance(a1, Chain):
                        if not a1._equals(a2, bijection=bijection):
                            return False
                    elif isinstance(a1, list):
                        assert t1 is Push or t1 is Launch
                        if tuple(a1) != tuple(a2):
                            return False
                    elif isinstance(a1, dict):
                        assert t1 is Guard
                        if len(a1) != len(a2):
                            return False
                        for k, v in a1.items():
                            try:
                                if v != a2[k]:
                                    return False
                            except KeyError:
                                return False
                    else:
                        if not a1 == a2:
                            return False
            return False

    def __eq__(self, other):
        return isinstance(other, Chain) and self._equals(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __add__(self, other):
        if not isinstance(other, Chain):
            raise TypeError("Chains can only be extended by other chains!")
        self._assert_continuable()
        s = Chain()
        s._proto = self._proto + other._proto
        s._targets = self._targets | other._targets
        s._can_continue = other._can_continue
        return s

    def print(self, out):
        out.write("Chain ")
        out.write(str(id(self)))
        out.write(":")
        for t, *args in self._proto:
            out.write(f"\n ")
            t.print_proto(out, *args)

    def __len__(self):
        return len(self._proto)

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
        Appends a prototype of an unconditional jump instruction to this chain.
        The chain cannot be continued after this.
        :param target: The chain to jump to.
        """
        # According to the semantics, there cannot be an error in evaluating Truth():
        self.append_guard({terms.CBool(True): target}, None)

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

    def append_pop(self, on_error):
        """
        Appends a prototype of a Pop instruction to this chain.
        The chain cannot be continued after a pop instruction.
        :param on_error: The chain to jump to if the instruction causes an error.
        """
        self._assert_continuable()
        check_type(on_error, Chain)
        self._proto.append((Pop, on_error))
        self._can_continue = False
        self._targets.add(on_error)

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
            entries[c] = offset
            offset += len(c)
            if c._can_continue:
                offset += 1
            chains.extend((t for t in c._targets if t is not None))

        instructions = []
        offset = 0

        for c in entries.keys(): # Enumerates the chains in the order they were inserted, guaranteeing that they start
                                 # exactly at the recorded offsets.
            for t, *args in c._proto:

                *args, on_error = args
                if on_error is None:
                    on_error = -1
                else:
                    on_error = entries[on_error]

                if t is Update:
                    ref, expression = args
                    instructions.append(Update(ref, expression, offset + 1, on_error))
                elif t is Guard:
                    alternatives, = args
                    instructions.append(Guard({condition: entries[chain] for condition, chain in alternatives.items()}, on_error))
                elif t is Push:
                    entry, expressions = args
                    instructions.append(Push(entry, expressions, offset + 1, on_error))
                elif t is Launch:
                    entry, expressions = args
                    instructions.append(Launch(entry, expressions, offset + 1, on_error))
                elif t is Pop:
                    instructions.append(Pop(on_error))
                else:
                    raise NotImplementedError("Bug in Chain.compile: The instruction type {} "
                                              "has not been taken into account for compilation yet!".format(t))
                offset += 1

            if c._can_continue:
                # TODO: this should probably be done in the first loop above!
                instructions.append(Guard({}, offset))
                offset += 1

        return StackProgram(instructions)
