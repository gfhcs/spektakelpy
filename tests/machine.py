import unittest

from engine.core.atomic import type_object
from engine.core.exceptions import VException
from engine.core.interaction import InteractionState, Interaction, num_interactions_possible
from engine.core.machine import TaskStatus, MachineState
from engine.core.none import value_none
from engine.core.primitive import VBool, VInt, VFloat, VStr
from engine.core.property import OrdinaryProperty
from engine.core.type import Type
from engine.exploration import explore, schedule_nonzeno
from engine.stack.exceptions import VTypeError
from engine.stack.frame import Frame
from engine.stack.instructionset import Update, Pop, Guard, Push, Launch
from engine.stack.procedure import StackProcedure
from engine.stack.program import StackProgram, ProgramLocation
from engine.stack.state import StackState
from lang.spek.data.bound import BoundProcedure
from lang.spek.data.classes import Class
from lang.spek.data.exceptions import JumpType
from lang.spek.data.references import FrameReference, ReturnValueReference, FieldReference
from lang.spek.data.terms import CInt, CBool, ArithmeticBinaryOperation, ArithmeticBinaryOperator, Read, CRef, \
    UnaryPredicateTerm, UnaryPredicate, ITask, CNone, CFloat, CString, UnaryOperation, \
    UnaryOperator, BooleanBinaryOperation, BooleanBinaryOperator, Comparison, ComparisonOperator, \
    IsInstance, NewTuple, NewList, NewDict, NewJumpError, NewNamespace, Lookup, NewProcedure, \
    NewProperty, NewClass, CTerm, LoadAttrCase, StoreAttrCase, Callable, Project
from lang.spek.data.values import VTuple, VList, VNamespace, VDict
from state_space.lts import state_space


class TestSpektakelMachine(unittest.TestCase):
    """
    This class is for testing Spektakelpy's virtual machine.
    """

    def initialize_machine(self, p, num_fvars=0):
        """
        Constructs the default initial state of the virtual machine.
        :param p: The StackProgram that should be executed by the machine.
        :param num_fvars: The number of variables to allocate on the initial stack frame.
        :return: A MachineState object.
        """
        frames = [Frame(ProgramLocation(p, 0), [value_none] * num_fvars)]
        m = StackState(TaskStatus.RUNNING, frames)
        return MachineState([m, *(InteractionState(i) for i in Interaction if i != Interaction.NEVER)])

    def explore(self, p, s0=None):
        """
        Computes the state space of the default machine for the given StackProgram.
        :param p: The StackProgram for which to explore the state space.
        :param s0: The initial MachineState for the state_space. If this is omitted, self.initialize_machine will be called.
        :return: A tuple (lts, states, internal, external), where lts is an LTS, and states contains all the states
                 of this LTS, whereas 'internal' and 'external' contain all the internal transitions and interaction
                 transitions respectively.
        """

        if s0 is None:
            s0 = self.initialize_machine(p)

        lts = state_space(explore(s0, scheduler=schedule_nonzeno))
        states = []
        internal, external = [], []
        visited = set()
        agenda = [lts.initial]
        while len(agenda) > 0:
            s = agenda.pop()
            if id(s) not in visited:
                visited.add(id(s))
                states.append(s)
                for t in s.transitions:
                    if isinstance(s.content.task_states[t.label], InteractionState):
                        external.append(t)
                    else:
                        internal.append(t)

                    agenda.append(t.target)

        return lts, states, internal, external

    def test_empty(self):
        """
        Tests the execution of an empty stack program.
        """
        p = StackProgram([])
        _, states, internal, external = self.explore(p)

        self.assertEqual(len(states), 1)
        self.assertEqual(len(internal), 0)

    def test_update_success(self):
        """
        Tests the successful execution of Update instructions.
        """

        p = StackProgram([Update(CRef(FrameReference(0)), CInt(42), 1, 1),
                          Guard({}, 1)])
        _, states, internal, external = self.explore(p, self.initialize_machine(p, 1))

        self.assertEqual(len(states), 2)
        self.assertEqual(len(internal), 1)
        self.assertEqual(len(external), num_interactions_possible)

        self.assertEqual(int(states[1].content.task_states[0].stack[0][0]), 42)
        self.assertEqual(states[1].content.task_states[0].exception, value_none)

    def test_update_failure(self):
        """
        Tests the errors raised by failing execution of the Update instruction.
        """

        p = StackProgram([Update(CRef(FrameReference(1)), Read(CRef(FrameReference(2))), 1, 1),
                          Guard({}, 1)])
        _, states, internal, external = self.explore(p, self.initialize_machine(p, 1))

        self.assertEqual(len(states), 2)
        self.assertEqual(len(internal), 1)

        self.assertEqual(states[1].content.task_states[0].stack[0][0], value_none)
        self.assertIsNot(states[1].content.task_states[0].exception, None)

    def test_guard_success(self):
        """
        Tests the successful execution of Guard instructions.
        """

        false = CBool(False)
        true = CBool(True)

        p = StackProgram([Guard({false: 1, true: 2}, 1),
                          Guard({}, 2),
                          Guard({true: 3}, 1),
                          Guard({false: 4}, 1),
                          Guard({true: 5}, 1)])
        _, states, internal, external = self.explore(p, self.initialize_machine(p))

        self.assertEqual(len(states), 2)
        self.assertEqual(len(internal), 1)
        self.assertEqual(len(external), num_interactions_possible)

    def test_guard_failure(self):
        """
        Tests the errors raised by failing execution of the Guard instruction.
        """

        p = StackProgram([Guard({CBool(False): 1, CBool(True): 34634}, 1),
                          Guard({}, 1)])
        _, states, internal, external = self.explore(p, self.initialize_machine(p))

        self.assertEqual(len(states), 2)
        self.assertEqual(len(internal), 1)
        self.assertEqual(len(external), num_interactions_possible)

        self.assertTrue(all(not isinstance(t, StackState) for t in states[1].content.task_states))

    def test_pop_success(self):
        """
        Tests the execution of Pop instructions.
        """

        p = StackProgram([Pop(42)])
        _, states, internal, external = self.explore(p, self.initialize_machine(p, 1))

        self.assertEqual(len(states), 2)
        self.assertEqual(len(internal), 1)
        self.assertEqual(len(external), num_interactions_possible)

        self.assertEqual(len(states[0].content.task_states[0].stack), 1)
        self.assertTrue(all(not isinstance(t, StackState) for t in states[-1].content.task_states))

    def test_pop_failure(self):
        """
        Tests the errors raised by failing execution of the Update instruction.
        """
        p = StackProgram([Pop(42), Pop(42)])
        _, states, internal, external = self.explore(p, self.initialize_machine(p))

        self.assertEqual(len(states), 2)
        self.assertEqual(len(internal), 1)

        self.assertEqual(len(states[0].content.task_states[0].stack), 1)
        self.assertTrue(all(not isinstance(t, StackState) for t in states[-1].content.task_states))

    def test_push_success(self):
        """
        Tests the successful execution of Push instructions.
        """

        q = StackProgram([Update(CRef(ReturnValueReference()),
                                 ArithmeticBinaryOperation(ArithmeticBinaryOperator.PLUS,
                                                           Read(CRef(FrameReference(0))), CInt(1)), 1, 1),
                                        Pop(42)])

        q = StackProcedure(1, ProgramLocation(q, 0))

        p = StackProgram([Push(Callable(Read(CRef(FrameReference(0)))), [CInt(42)], 1, 1),
                          Guard({}, 1)])

        state0 = self.initialize_machine(p, 1)
        list(state0.task_states)[0].stack[0][0] = q

        _, states, internal, external = self.explore(p, state0)

        self.assertEqual(len(states), 2)
        self.assertEqual(len(internal), 1)
        self.assertEqual(len(external), num_interactions_possible)

        self.assertEqual(int(states[1].content.task_states[0].returned), 43)
        self.assertEqual(states[1].content.task_states[0].exception, value_none)

    def test_push_failure(self):
        """
        Tests the errors raised by failing execution of the Push instruction.
        """

        q = StackProgram([Update(CRef(ReturnValueReference()),
                                 ArithmeticBinaryOperation(ArithmeticBinaryOperator.PLUS,
                                                           Read(CRef(FrameReference(0))), CInt(1)), 1, 1),
                                        Pop(42)])

        q = StackProcedure(1, ProgramLocation(q, 0))

        p = StackProgram([Push(Callable(Read(CRef(FrameReference(17)))), [CInt(42)], 1, 1),
                          Guard({}, 1)])

        state0 = self.initialize_machine(p, 1)
        list(state0.task_states)[0].stack[0][0] = q

        _, states, internal, external = self.explore(p, state0)

        self.assertEqual(len(states), 2)
        self.assertEqual(len(internal), 1)
        self.assertEqual(len(external), num_interactions_possible)

        self.assertIsNot(states[1].content.task_states[0].exception, None)

    def test_launch_success(self):
        """
        Tests the successful execution of Launch instructions.
        """

        q = StackProgram([Update(CRef(ReturnValueReference()),
                                 ArithmeticBinaryOperation(ArithmeticBinaryOperator.PLUS,
                                                           Read(CRef(FrameReference(0))), CInt(1)), 1, 1),
                          Guard({}, 1)])

        q = StackProcedure(1, ProgramLocation(q, 0))

        p = StackProgram([Launch(Callable(Read(CRef(FrameReference(0)))), [CInt(42)], 1, 1),
                          Guard({}, 1)])

        state0 = self.initialize_machine(p, 1)
        list(state0.task_states)[0].stack[0][0] = q

        _, states, internal, external = self.explore(p, state0)

        self.assertEqual(len(states), 3)
        self.assertEqual(len(internal), 2)
        self.assertEqual(len(external), num_interactions_possible)

        self.assertIsNot(states[1].content.task_states[0].returned, None)
        t = states[-1].content.task_states[0].returned
        idx = None
        for idx, tt in enumerate(states[1].content.task_states):
            if tt is t:
                break
        t = states[-1].content.task_states[idx]
        self.assertEqual(int(t.returned), 43)

    def test_launch_failure(self):
        """
        Tests the errors raised by failing execution of the Launch instruction.
        """

        q = StackProgram([Update(CRef(ReturnValueReference()),
                                 ArithmeticBinaryOperation(ArithmeticBinaryOperator.PLUS,
                                                           Read(CRef(FrameReference(0))), CInt(1)), 1, 1),
                                        Pop(42)])

        q = StackProcedure(1, ProgramLocation(q, 0))

        p = StackProgram([Launch(Callable(Read(CRef(FrameReference(17)))), [CInt(42)], 1, 1),
                          Guard({}, 1)])

        state0 = self.initialize_machine(p, 1)
        list(state0.task_states)[0].stack[0][0] = q

        _, states, internal, external = self.explore(p, state0)

        self.assertEqual(len(states), 2)
        self.assertEqual(len(internal), 1)
        self.assertEqual(len(external), num_interactions_possible)

        self.assertIsNot(states[1].content.task_states[0].exception, None)

    def test_intrinsic_success(self):
        """
        Tests the succesful execution of Intrinsic procedures.
        """

        p = StackProgram([Push(Callable(Read(CRef(FrameReference(1)))), [Read(CRef(FrameReference(0))), CInt(0)], 1, 1),
                          Guard({}, 1)])

        state0 = self.initialize_machine(p, 2)
        state0.task_states[0].stack[0][0] = VList(items=[VInt(42)])
        state0.task_states[0].stack[0][1] = VList.intrinsic_type.members["pop"]

        _, states, internal, external = self.explore(p, state0)

        self.assertEqual(len(states), 2)
        self.assertEqual(len(internal), 1)
        self.assertEqual(len(external), num_interactions_possible)

        self.assertEqual(int(states[1].content.task_states[0].returned), 42)
        self.assertEqual(states[1].content.task_states[0].exception, value_none)

    def test_intrinsic_failure(self):
        """
        Tests the errors raised by an IntrinsicProcedure.
        """

        p = StackProgram([Push(Callable(Read(CRef(FrameReference(1)))), [Read(CRef(FrameReference(0)))], 1, 1),
                          Guard({}, 1)])

        state0 = self.initialize_machine(p, 1)
        state0.task_states[0].stack[0][0] = VList(items=[])
        state0.task_states[0].stack[0][0] = VList.intrinsic_type.members["pop"]

        _, states, internal, external = self.explore(p, state0)

        self.assertEqual(len(states), 2)
        self.assertEqual(len(internal), 1)
        self.assertEqual(len(external), num_interactions_possible)

        self.assertIsNot(states[1].content.task_states[0].exception, None)

    def test_interaction1(self):
        """
        Tests the successful synchronization with interaction tasks.
        """

        ip = 0

        def program_sync(s):
            nonlocal ip
            t = FrameReference(0)
            instructions = [Update(CRef(t), ITask(s), ip + 1, ip),
                            Guard({UnaryPredicateTerm(UnaryPredicate.ISTERMINATED, Read(CRef(t))): ip + 2}, ip + 1)]
            try:
                return instructions
            finally:
                ip += len(instructions)

        p = StackProgram([*program_sync(Interaction.NEXT),
                          *program_sync(Interaction.NEXT),
                          *program_sync(Interaction.PREV),
                          *program_sync(Interaction.TICK),
                          *program_sync(Interaction.NEXT),
                          *program_sync(Interaction.TICK),
                          *program_sync(Interaction.PREV)])

        s0 = self.initialize_machine(p, 1)
        _, states, internal, external = self.explore(p, s0)

        self.assertEqual(8 * num_interactions_possible, len(external))
        self.assertEqual(8, len(internal))
        self.assertEqual(16, len(states))

    def test_interaction2(self):
        """
        Tests the successful synchronization with interaction tasks.
        """

        ip = 0
        t1 = FrameReference(0)
        t2 = FrameReference(1)

        def program_sync(s):
            nonlocal ip
            t = FrameReference(0)
            instructions = [Update(CRef(t), ITask(s), ip + 1, ip),
                            Guard({UnaryPredicateTerm(UnaryPredicate.ISTERMINATED, Read(CRef(t))): ip + 2}, ip + 1)]
            try:
                return instructions
            finally:
                ip += len(instructions)

        p = StackProgram([*program_sync(Interaction.NEXT),
                          Update(CRef(t1), ITask(Interaction.NEXT), ip + 1, ip),
                          Update(CRef(t2), ITask(Interaction.PREV), ip + 2, ip + 1),
                          Guard({UnaryPredicateTerm(UnaryPredicate.ISTERMINATED, Read(CRef(t1))): ip + 3,
                                 UnaryPredicateTerm(UnaryPredicate.ISTERMINATED, Read(CRef(t2))): ip}, ip + 3),
                          Update(CRef(t1), CNone(), ip + 4, ip),
                          Update(CRef(t2), CNone(), ip + 5, ip),
                         ])

        s0 = self.initialize_machine(p, 2)
        s0.task_states[0].stack[0][0] = value_none
        s0.task_states[0].stack[0][1] = value_none
        lts, states, internal, external = self.explore(p, s0)

        # print(lts2str(lts))

        self.assertEqual(7, len(states))
        self.assertEqual(3 * num_interactions_possible, len(external))
        self.assertEqual(4, len(internal))

    def test_CInt(self):
        """
        Tests the successful evaluation of CInt terms.
        """

        p = StackProgram([Update(CRef(FrameReference(0)), CInt(42), 1, 1),
                                  Guard({}, 1)])
        _, states, internal, external = self.explore(p, self.initialize_machine(p, 1))
        result = states[-1].content.task_states[0].stack[0][0]
        self.assertEqual(42, int(result))

    def test_CFloat(self):
        """
        Tests the successful evaluation of CFloat terms.
        """
        p = StackProgram([Update(CRef(FrameReference(0)), CFloat(3.1415926), 1, 1),
                                  Guard({}, 1)])
        _, states, internal, external = self.explore(p, self.initialize_machine(p, 1))
        result = states[-1].content.task_states[0].stack[0][0]
        self.assertEqual(3.1415926, float(result))

    def test_CBool(self):
        """
        Tests the successful evaluation of CFloat terms.
        """
        p = StackProgram([Update(CRef(FrameReference(0)), CBool(False), 1, 1),
                                  Guard({}, 1)])
        _, states, internal, external = self.explore(p, self.initialize_machine(p, 1))
        result = states[-1].content.task_states[0].stack[0][0]
        self.assertEqual(VBool(False), result)

    def test_CNone(self):
        """
        Tests the successful evaluation of CFloat terms.
        """

        p = StackProgram([Update(CRef(FrameReference(0)), CNone(), 1, 1),
                          Guard({}, 1)])
        _, states, internal, external = self.explore(p, self.initialize_machine(p, 1))

        result = states[-1].content.task_states[0].stack[0][0]

        self.assertIs(value_none, result)

    def test_CString(self):
        """
        Tests the successful evaluation of CFloat terms.
        """
        p = StackProgram([Update(CRef(FrameReference(0)), CString("Hello World"), 1, 1),
                                  Guard({}, 1)])
        _, states, internal, external = self.explore(p, self.initialize_machine(p, 1))
        result = states[-1].content.task_states[0].stack[0][0]
        self.assertEqual("Hello World", str(result))

    def test_UnaryOperation(self):

        """
        Tests the successful evaluation of ArithmeticUnaryOperation terms.
        """

        cases = [(UnaryOperation(UnaryOperator.MINUS, CInt(42)), VInt(-42)),
                 (UnaryOperation(UnaryOperator.INVERT, CInt(42)), VInt(~42)),
                 (UnaryOperation(UnaryOperator.NOT, CBool(True)), VBool(False)),
                 (UnaryOperation(UnaryOperator.MINUS, CFloat(42.0)), VFloat(-42.0))]

        for idx, (term, value) in enumerate(cases):
            with self.subTest(idx=idx, term=term):
                p = StackProgram([Update(CRef(FrameReference(0)), term, 1, 1),
                                  Guard({}, 1)])
                _, states, _, _ = self.explore(p, self.initialize_machine(p, 1))
                result = states[-1].content.task_states[0].stack[0][0]
                self.assertEqual(value.seal(), result)

    def test_ArithmeticBinaryOperation(self):

        """
        Tests the successful evaluation of ArithmeticBinaryOperation terms.
        """

        cases = [(ArithmeticBinaryOperation(ArithmeticBinaryOperator.PLUS, CInt(42), CInt(11)), VInt(53)),
                 (ArithmeticBinaryOperation(ArithmeticBinaryOperator.MINUS, CInt(42), CInt(11)), VInt(31)),
                 (ArithmeticBinaryOperation(ArithmeticBinaryOperator.TIMES, CInt(42), CInt(11)), VInt(462)),
                 (ArithmeticBinaryOperation(ArithmeticBinaryOperator.OVER, CInt(42), CInt(11)), VFloat(42 / 11)),
                 (ArithmeticBinaryOperation(ArithmeticBinaryOperator.MODULO, CInt(42), CInt(11)), VInt(9)),
                 (ArithmeticBinaryOperation(ArithmeticBinaryOperator.POWER, CInt(42), CInt(11)), VInt(42 ** 11)),
                 (ArithmeticBinaryOperation(ArithmeticBinaryOperator.INTOVER, CInt(42), CInt(11)), VInt(3)),
                 ]

        for idx, (term, value) in enumerate(cases):
            with self.subTest(idx=idx, term=term):
                p = StackProgram([Update(CRef(FrameReference(0)), term, 1, 1),
                                  Guard({}, 1)])
                _, states, _, _ = self.explore(p, self.initialize_machine(p, 1))
                result = states[-1].content.task_states[0].stack[0][0]
                self.assertEqual(value.seal(), result)

    def test_BooleanBinaryOperation(self):

        """
        Tests the successful evaluation of BooleanBinaryOperation terms.
        """

        cases = [(BooleanBinaryOperation(BooleanBinaryOperator.AND, CBool(False), CBool(False)), VBool(False)),
                 (BooleanBinaryOperation(BooleanBinaryOperator.AND, CBool(False), CBool(True)), VBool(False)),
                 (BooleanBinaryOperation(BooleanBinaryOperator.AND, CBool(True), CBool(False)), VBool(False)),
                 (BooleanBinaryOperation(BooleanBinaryOperator.AND, CBool(True), CBool(True)), VBool(True)),
                 (BooleanBinaryOperation(BooleanBinaryOperator.OR, CBool(False), CBool(False)), VBool(False)),
                 (BooleanBinaryOperation(BooleanBinaryOperator.OR, CBool(False), CBool(True)), VBool(True)),
                 (BooleanBinaryOperation(BooleanBinaryOperator.OR, CBool(True), CBool(False)), VBool(True)),
                 (BooleanBinaryOperation(BooleanBinaryOperator.OR, CBool(True), CBool(True)), VBool(True))
                 ]

        for term, value in cases:
            with self.subTest(term=term):
                p = StackProgram([Update(CRef(FrameReference(0)), term, 1, 1),
                                  Guard({}, 1)])
                _, states, _, _ = self.explore(p, self.initialize_machine(p, 1))
                result = states[-1].content.task_states[0].stack[0][0]
                self.assertEqual(value.seal(), result)

    def test_Comparison(self):

        """
        Tests the successful evaluation of Comparison terms.
        """

        cases = [(Comparison(ComparisonOperator.EQ, CInt(42), CFloat(42.0)), VBool(True)),
                 (Comparison(ComparisonOperator.EQ, CInt(42), CFloat(43.0)), VBool(False)),
                 (Comparison(ComparisonOperator.NEQ, CInt(42), CFloat(42.0)), VBool(False)),
                 (Comparison(ComparisonOperator.NEQ, CInt(42), CFloat(43.0)), VBool(True)),
                 (Comparison(ComparisonOperator.LESS, CInt(42), CFloat(374895.0)), VBool(True)),
                 (Comparison(ComparisonOperator.LESS, CInt(42), CFloat(-43.0)), VBool(False)),
                 (Comparison(ComparisonOperator.LESSOREQUAL, CInt(42), CInt(42)), VBool(True)),
                 (Comparison(ComparisonOperator.LESSOREQUAL, CInt(42), CFloat(-43.0)), VBool(False)),
                 (Comparison(ComparisonOperator.GREATER, CInt(42), CFloat(374895.0)), VBool(False)),
                 (Comparison(ComparisonOperator.GREATER, CInt(42), CFloat(-43.0)), VBool(True)),
                 (Comparison(ComparisonOperator.GREATEROREQUAL, CInt(42), CInt(42)), VBool(True)),
                 (Comparison(ComparisonOperator.GREATEROREQUAL, CFloat(-43.0), CInt(42)), VBool(False)),
                 (Comparison(ComparisonOperator.IS, CNone(), CNone()), VBool(True)),
                 (Comparison(ComparisonOperator.IS, CInt(42), CNone()), VBool(False)),
                 (Comparison(ComparisonOperator.ISNOT, CNone(), CNone()), VBool(False)),
                 (Comparison(ComparisonOperator.ISNOT, CInt(42), CNone()), VBool(True)),
                 (Comparison(ComparisonOperator.IN, CString("a"), CString("Hallo")), VBool(True)),
                 (Comparison(ComparisonOperator.IN, CString("a"), CString("Hello")), VBool(False)),
                 (Comparison(ComparisonOperator.NOTIN, CString("a"), CString("Hallo")), VBool(False)),
                 (Comparison(ComparisonOperator.NOTIN, CString("a"), CString("Hello")), VBool(True))
                 ]

        for idx, (term, value) in enumerate(cases):
            with self.subTest(idx=idx, term=term):
                p = StackProgram([Update(CRef(FrameReference(0)), term, 1, 1),
                                  Guard({}, 1)])
                _, states, _, _ = self.explore(p, self.initialize_machine(p, 1))
                result = states[-1].content.task_states[0].stack[0][0]
                self.assertEqual(value, result)

    def test_UnaryPredicateTerm(self):

        """
        Tests the successful evaluation of UnaryPredicateTerm terms.
        """

        cases = [(UnaryPredicateTerm(UnaryPredicate.ISTERMINATED, ITask(Interaction.NEXT)), VBool(False)),
                 (UnaryPredicateTerm(UnaryPredicate.ISCALLABLE, CInt(42)), VBool(False)),
                 (UnaryPredicateTerm(UnaryPredicate.ISCALLABLE, Read(CRef(FrameReference(0)))), VBool(True)),
                 (UnaryPredicateTerm(UnaryPredicate.ISEXCEPTION, CInt(42)), VBool(False)),
                 (UnaryPredicateTerm(UnaryPredicate.ISEXCEPTION, CTerm(VTypeError("Just for testing."))), VBool(True))
                 ]

        for idx, (term, value) in enumerate(cases):
            with self.subTest(idx=idx, term=term):
                p = StackProgram([Update(CRef(FrameReference(0)), term, 1, 1),
                                  Guard({}, 1)])
                s0 = self.initialize_machine(p, 1)
                s0.task_states[0].stack[0][0] = VList.intrinsic_type.members["append"]
                _, states, _, _ = self.explore(p, s0)
                result = states[-1].content.task_states[0].stack[0][0]
                self.assertEqual(value, result)

    def test_IsInstance(self):
        """
        Tests the successful evaluation of IsInstance terms.
        """

        cases = [(IsInstance(CInt(42), NewTuple(CTerm(VFloat.intrinsic_type), CTerm(VInt.intrinsic_type))), VBool(True)),
                 (IsInstance(CInt(42), CTerm(VFloat.intrinsic_type)), VBool(False))
                 ]

        for term, value in cases:
            with self.subTest(term=term):
                p = StackProgram([Update(CRef(FrameReference(0)), term, 1, 1),
                                  Guard({}, 1)])
                _, states, _, _ = self.explore(p, self.initialize_machine(p, 1))
                result = states[-1].content.task_states[0].stack[0][0]
                self.assertEqual(value.seal(), result)

    def test_Read(self):
        """
        Tests the successful evaluation of Read terms.
        """

        cases = [(Read(CRef(FrameReference(0))), VInt(42))]

        for term, value in cases:
            with self.subTest(term=term):
                p = StackProgram([Update(CRef(FrameReference(0)), term, 1, 1),
                                  Guard({}, 1)])
                s0 = self.initialize_machine(p, 1)
                s0.task_states[0].stack[0][0] = VInt(42)
                _, states, _, _ = self.explore(p, s0)
                result = states[-1].content.task_states[0].stack[0][0]
                self.assertEqual(value.seal(), result)

    def test_new(self):
        """
        Tests the successful evaluation of terms that create new objects.
        """

        cases = [(Comparison(ComparisonOperator.EQ, NewTuple(CInt(42), CInt(4711)), NewTuple(CInt(42), CInt(4711))), VBool(True)),
                 (IsInstance(NewList(), CTerm(VList.intrinsic_type)), VBool(True)),
                 (IsInstance(NewDict(), CTerm(VDict.intrinsic_type)), VBool(True)),
                 (UnaryPredicateTerm(UnaryPredicate.ISRETURN, NewJumpError(JumpType.RETURN)), VBool(True)),
                 (UnaryPredicateTerm(UnaryPredicate.ISBREAK, NewJumpError(JumpType.BREAK)), VBool(True)),
                 (UnaryPredicateTerm(UnaryPredicate.ISCONTINUE, NewJumpError(JumpType.CONTINUE)), VBool(True)),
                 (IsInstance(CTerm(VTypeError("Just a test.")), CTerm(VTypeError.intrinsic_type)), VBool(True))
                 ]

        for idx, (term, value) in enumerate(cases):
            with self.subTest(idx=idx, term=term):
                p = StackProgram([Update(CRef(FrameReference(0)), term, 1, 1),
                                  Guard({}, 1)])
                _, states, _, _ = self.explore(p, self.initialize_machine(p, 1))
                result = states[-1].content.task_states[0].stack[0][0]
                self.assertEqual(value.seal(), result)

    def test_namespace1(self):
        """
        Tests the successful evaluation of namespace-related terms.
        """
        cases = [(IsInstance(NewNamespace(), CTerm(VNamespace.intrinsic_type)), VBool(True)),
                 (Read(Lookup(CRef(FrameReference(0)), CString("hello"))), VInt(42))]

        for term, value in cases:
            with self.subTest(term=term):
                p = StackProgram([Update(CRef(FrameReference(0)), term, 1, 1),
                                  Guard({}, 1)])
                s0 = self.initialize_machine(p, 1)

                ns = VNamespace()
                ns[VStr("hello")] = VInt(42)

                s0.task_states[0].stack[0][0] = ns
                _, states, _, _ = self.explore(p, s0)
                result = states[-1].content.task_states[0].stack[0][0]
                self.assertEqual(value.seal(), result)

    def test_namespace2(self):
        """
        Tests the successful evaluation of namespace-related terms.
        """

        p = StackProgram([Update(CRef(FrameReference(0)), NewNamespace(), 1, 42),
                          Update(Lookup(CRef(FrameReference(0)), CString("x")), CInt(42), 2, 42),
                          Update(Lookup(CRef(FrameReference(0)), CString("y")), CInt(4711), 3, 42),
                          Update(CRef(FrameReference(0)), Read(CRef(FrameReference(0))), 4, 42),
                          Guard({}, 1)]
                         )

        state0 = self.initialize_machine(p, 1)

        _, states, internal, external = self.explore(p, state0)

        self.assertEqual(len(states), 2)
        self.assertEqual(len(internal), 1)
        self.assertEqual(len(external), num_interactions_possible)

        self.assertIsInstance(states[-1].content.task_states[0].stack[0][0], VNamespace)

    def test_procedure(self):
        """
        Tests the successful evaluation of procedure-related terms.
        """

        q = StackProgram([Update(CRef(ReturnValueReference()),
                                 ArithmeticBinaryOperation(ArithmeticBinaryOperator.PLUS,
                                                           Read(CRef(FrameReference(0))), CInt(1)), 1, 1),
                                        Pop(42)])

        p = StackProgram([Update(CRef(FrameReference(0)), NewProcedure(1, tuple(), q), 1, 3),
                          Push(Callable(Read(CRef(FrameReference(0)))), [CInt(42)], 2, 3),
                          Guard({}, 2)])

        state0 = self.initialize_machine(p, 1)

        _, states, internal, external = self.explore(p, state0)

        self.assertEqual(len(states), 2)
        self.assertEqual(len(internal), 1)
        self.assertEqual(len(external), num_interactions_possible)

        self.assertEqual(int(states[-1].content.task_states[0].returned), 43)

    def test_class(self):
        """
        Tests the successful evaluation of class-related terms.
        """

        g = StackProgram([Update(CRef(ReturnValueReference()), CInt(42), 1, 1), Pop(42)])
        s = StackProgram([Pop(42)])

        p = StackProgram([Update(CRef(FrameReference(0)), NewNamespace(), 1, 42),
                          Update(Lookup(CRef(FrameReference(0)), CString("test")), NewProperty(NewProcedure(1, tuple(), g), NewProcedure(2, tuple(), s)), 2, 42),
                          Update(CRef(FrameReference(0)), NewClass("C", [CTerm(type_object)], Read(CRef(FrameReference(0)))), 3, 42),
                          Guard({}, 1)])

        state0 = self.initialize_machine(p, 1)

        _, states, internal, external = self.explore(p, state0)

        self.assertEqual(len(states), 2)
        self.assertEqual(len(internal), 1)
        self.assertEqual(len(external), num_interactions_possible)
        self.assertIsInstance(states[-1].content.task_states[0].stack[0][0], Type)

    def test_LoadAttrCase(self):
        """
        Tests the successful evaluation of LoadAttrCase terms.
        """
        method = StackProgram([Update(CRef(ReturnValueReference()), CInt(42), 1, 1), Pop(42)])
        method = StackProcedure(1, ProgramLocation(method, 0))

        g = StackProcedure(1, ProgramLocation(StackProgram([Update(CRef(ReturnValueReference()), CInt(42), 1, 1), Pop(42)]), 0))
        s = StackProcedure(2, ProgramLocation(StackProgram([Pop(42)]), 0))
        property = OrdinaryProperty(g, s)

        members = {"method": method, "property": property}
        c = Class("C", [type_object], ["x"], members)

        i = c.new()

        cases = (("x", (True, VBool(False), value_none)),
                 ("method", (False, VBool(False), VInt(42))),
                 ("property", (False, VBool(True), VInt(42))))

        for identifier, value in cases:
            with self.subTest(identifier=identifier):

                direct, v1, v2 = value
                p = [Update(CRef(FrameReference(0)), LoadAttrCase(CTerm(i), identifier), 1, 42)]

                if not direct:
                    p.append(Push(Callable(Project(Read(CRef(FrameReference(0))), CInt(1))), [], len(p) + 1, 42))
                    p.append(Update(CRef(FrameReference(0)), NewTuple(Project(Read(CRef(FrameReference(0))), CInt(0)), Read(CRef(ReturnValueReference()))), len(p) + 1, 42))

                p = StackProgram([*p, Guard({}, len(p))])

                _, states, internal, external = self.explore(p, self.initialize_machine(p, 1))

                self.assertEqual(len(states), 2)
                self.assertEqual(len(internal), 1)
                self.assertEqual(len(external), num_interactions_possible)
                self.assertTrue(states[-1].content.task_states[0].stack[0][0].cequals(VTuple(v1, v2)))

    def test_StoreAttrCase(self):
        """
        Tests the successful evaluation of StoreAttrCase terms.
        """
        method = StackProgram([Update(CRef(ReturnValueReference()), CInt(42), 1, 1), Pop(42)])
        method = StackProcedure(1, ProgramLocation(method, 0))

        g = StackProcedure(1, ProgramLocation(StackProgram([Update(CRef(ReturnValueReference()), CInt(42), 1, 1), Pop(42)]), 0))
        s = StackProcedure(2, ProgramLocation(StackProgram([Pop(42)]), 0))
        property = OrdinaryProperty(g, s)

        members = {"method": method, "property": property}
        c = Class("C", [type_object], ["x"], members)

        i = c.new()

        cases = (("x", FieldReference),
                 ("method", VException),
                 ("property", BoundProcedure(s, i)))

        for identifier, value in cases:
            with self.subTest(identifier=identifier):
                p = StackProgram([Update(CRef(FrameReference(0)), StoreAttrCase(CTerm(i), identifier), 1, 42),
                                  Guard({}, 1)])

                _, states, internal, external = self.explore(p, self.initialize_machine(p, 1))

                self.assertEqual(len(states), 2)
                self.assertEqual(len(internal), 1)
                self.assertEqual(len(external), num_interactions_possible)
                result = states[-1].content.task_states[0].stack[0][0]

                if isinstance(value, type):
                    self.assertIsInstance(result, value)
                else:
                    self.assertTrue(result.bequals(value, {}))





