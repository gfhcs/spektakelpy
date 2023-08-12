import unittest

from engine.exploration import explore, state_space, schedule_nonzeno
from engine.functional.reference import FrameReference, ReturnValueReference
from engine.functional.terms import CInt, CBool, ArithmeticBinaryOperation, ArithmeticBinaryOperator, Read, CRef, \
    UnaryPredicateTerm, UnaryPredicate, ITask, CNone, CFloat, CString, ArithmeticUnaryOperation, \
    ArithmeticUnaryOperator, BooleanBinaryOperation, BooleanBinaryOperator, Comparison, ComparisonOperator, \
    NewTypeError, IsInstance, NewTuple, CType, NewList, NewDict, NewJumpError, NewNamespace, Lookup, NewProcedure, \
    NumArgs
from engine.functional.types import TBuiltin
from engine.functional.values import VNone, VProcedure, VList, VInt, VFloat, VBool, VTuple, VReturnError, \
    VBreakError, VNamespace, VStr
from engine.machine import MachineState
from engine.task import TaskStatus
from engine.tasks.instructions import StackProgram, ProgramLocation, Update, Pop, Guard, Push, Launch
from engine.tasks.interaction import InteractionState, Interaction
from engine.tasks.stack import StackState, Frame
from util.lts import lts2str


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

        frames = [Frame(ProgramLocation(p, 0), [VNone.instance] * num_fvars)]

        m = StackState(TaskStatus.RUNNING, frames)

        isymbols = [Interaction.NEXT, Interaction.PREV, Interaction.TICK]
        istates = (InteractionState(i) for i in isymbols)

        return MachineState([m, *istates])

    def explore(self, p, s0=None):
        """
        Computes the state space of the default machine for the given StackProgram.
        :param p: The StackProgram for which to explore the state space.
        :param s0: The initial MachineState for the exploration. If this is omitted, self.initialize_machine will be called.
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

        p = StackProgram([Update(FrameReference(0), CInt(42), 1, 1),
                          Guard({}, 1)])
        _, states, internal, external = self.explore(p, self.initialize_machine(p, 1))

        self.assertEqual(len(states), 2)
        self.assertEqual(len(internal), 1)
        self.assertEqual(len(external), 3)

        self.assertEqual(int(states[1].content.task_states[0].stack[0][0]), 42)
        self.assertIs(states[1].content.task_states[0].exception, None)

    def test_update_failure(self):
        """
        Tests the errors raised by failing execution of the Update instruction.
        """
        p = StackProgram([Update(FrameReference(1), CInt(42), 1, 1),
                          Guard({}, 1)])
        _, states, internal, external = self.explore(p, self.initialize_machine(p, 1))

        self.assertEqual(len(states), 2)
        self.assertEqual(len(internal), 1)

        self.assertEqual(states[1].content.task_states[0].stack[0][0], VNone.instance)
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
        self.assertEqual(len(external), 3)

    def test_guard_failure(self):
        """
        Tests the errors raised by failing execution of the Guard instruction.
        """
        false = CBool(False)
        true = CBool(True)

        p = StackProgram([Guard({false: 1, true: 34634}, 1),
                          Guard({}, 1)])
        _, states, internal, external = self.explore(p, self.initialize_machine(p))

        self.assertEqual(len(states), 2)
        self.assertEqual(len(internal), 1)
        self.assertEqual(len(external), 3)

        self.assertIsNot(states[1].content.task_states[0].exception, None)

    def test_pop_success(self):
        """
        Tests the execution of Pop instructions.
        """

        p = StackProgram([Pop()])
        _, states, internal, external = self.explore(p, self.initialize_machine(p, 1))

        self.assertEqual(len(states), 2)
        self.assertEqual(len(internal), 1)
        self.assertEqual(len(external), 3)

        self.assertEqual(len(states[0].content.task_states[0].stack), 1)
        self.assertEqual(len(states[1].content.task_states[0].stack), 0)

    def test_pop_failure(self):
        """
        Tests the errors raised by failing execution of the Update instruction.
        """
        p = StackProgram([Pop(), Pop()])
        _, states, internal, external = self.explore(p, self.initialize_machine(p))

        self.assertEqual(len(states), 2)
        self.assertEqual(len(internal), 1)

        self.assertEqual(len(states[0].content.task_states[0].stack), 1)
        self.assertEqual(len(states[1].content.task_states[0].stack), 0)

    def test_push_success(self):
        """
        Tests the successful execution of Push instructions.
        """

        q = StackProgram([Update(ReturnValueReference(),
                                               ArithmeticBinaryOperation(ArithmeticBinaryOperator.PLUS,
                                                                         Read(CRef(FrameReference(0))), CInt(1)), 1, 1),
                                        Pop()])

        q = VProcedure(1, ProgramLocation(q, 0))

        p = StackProgram([Push(Read(CRef(FrameReference(0))), [CInt(42)], 1, 1),
                          Guard({}, 1)])

        state0 = self.initialize_machine(p, 1)
        list(state0.task_states)[0].stack[0][0] = q

        _, states, internal, external = self.explore(p, state0)

        self.assertEqual(len(states), 2)
        self.assertEqual(len(internal), 1)
        self.assertEqual(len(external), 3)

        self.assertEqual(int(states[1].content.task_states[0].returned), 43)
        self.assertIs(states[1].content.task_states[0].exception, None)

    def test_push_failure(self):
        """
        Tests the errors raised by failing execution of the Push instruction.
        """

        q = StackProgram([Update(ReturnValueReference(),
                                               ArithmeticBinaryOperation(ArithmeticBinaryOperator.PLUS,
                                                                         Read(CRef(FrameReference(0))), CInt(1)), 1, 1),
                                        Pop()])

        q = VProcedure(1, ProgramLocation(q, 0))

        p = StackProgram([Push(Read(CRef(FrameReference(17))), [CInt(42)], 1, 1),
                          Guard({}, 1)])

        state0 = self.initialize_machine(p, 1)
        list(state0.task_states)[0].stack[0][0] = q

        _, states, internal, external = self.explore(p, state0)

        self.assertEqual(len(states), 2)
        self.assertEqual(len(internal), 1)
        self.assertEqual(len(external), 3)

        self.assertIsNot(states[1].content.task_states[0].exception, None)

    def test_launch_success(self):
        """
        Tests the successful execution of Launch instructions.
        """

        q = StackProgram([Update(ReturnValueReference(),
                                               ArithmeticBinaryOperation(ArithmeticBinaryOperator.PLUS,
                                                                         Read(CRef(FrameReference(0))), CInt(1)), 1, 1),
                                        Pop()])

        q = VProcedure(1, ProgramLocation(q, 0))

        p = StackProgram([Launch(Read(CRef(FrameReference(0))), [CInt(42)], 1, 1),
                          Guard({}, 1)])

        state0 = self.initialize_machine(p, 1)
        list(state0.task_states)[0].stack[0][0] = q

        _, states, internal, external = self.explore(p, state0)

        self.assertEqual(len(states), 3)
        self.assertEqual(len(internal), 2)
        self.assertEqual(len(external), 3)

        self.assertIsNot(states[1].content.task_states[0].returned, None)
        t = states[1].content.task_states[0].returned
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

        q = StackProgram([Update(ReturnValueReference(),
                                               ArithmeticBinaryOperation(ArithmeticBinaryOperator.PLUS,
                                                                         Read(CRef(FrameReference(0))), CInt(1)), 1, 1),
                                        Pop()])

        q = VProcedure(1, ProgramLocation(q, 0))

        p = StackProgram([Launch(Read(CRef(FrameReference(17))), [CInt(42)], 1, 1),
                          Guard({}, 1)])

        state0 = self.initialize_machine(p, 1)
        list(state0.task_states)[0].stack[0][0] = q

        _, states, internal, external = self.explore(p, state0)

        self.assertEqual(len(states), 2)
        self.assertEqual(len(internal), 1)
        self.assertEqual(len(external), 3)

        self.assertIsNot(states[1].content.task_states[0].exception, None)

    def test_intrinsic_success(self):
        """
        Tests the succesful execution of Intrinsic procedures.
        """

        p = StackProgram([Push(Read(CRef(FrameReference(1))), [Read(CRef(FrameReference(0))), CInt(0)], 1, 1),
                          Guard({}, 1)])

        state0 = self.initialize_machine(p, 2)
        state0.task_states[0].stack[0][0] = VList(items=[VInt(42)])
        state0.task_states[0].stack[0][1] = VList.pop

        _, states, internal, external = self.explore(p, state0)

        self.assertEqual(len(states), 2)
        self.assertEqual(len(internal), 1)
        self.assertEqual(len(external), 3)

        self.assertEqual(int(states[1].content.task_states[0].returned), 42)
        self.assertIs(states[1].content.task_states[0].exception, None)

    def test_intrinsic_failure(self):
        """
        Tests the errors raised by an IntrinsicProcedure.
        """

        p = StackProgram([Push(Read(CRef(FrameReference(1))), [Read(CRef(FrameReference(0)))], 1, 1),
                          Guard({}, 1)])

        state0 = self.initialize_machine(p, 1)
        state0.task_states[0].stack[0][0] = VList(items=[])
        state0.task_states[0].stack[0][0] = VList.pop

        _, states, internal, external = self.explore(p, state0)

        self.assertEqual(len(states), 2)
        self.assertEqual(len(internal), 1)
        self.assertEqual(len(external), 3)

        self.assertIsNot(states[1].content.task_states[0].exception, None)

    def test_interaction1(self):
        """
        Tests the successful synchronization with interaction tasks.
        """

        ip = 0

        def program_sync(s):
            nonlocal ip
            t = FrameReference(0)
            instructions = [Update(t, ITask(s), ip + 1, ip),
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

        self.assertEqual(24, len(external))
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
            instructions = [Update(t, ITask(s), ip + 1, ip),
                            Guard({UnaryPredicateTerm(UnaryPredicate.ISTERMINATED, Read(CRef(t))): ip + 2}, ip + 1)]
            try:
                return instructions
            finally:
                ip += len(instructions)

        p = StackProgram([*program_sync(Interaction.NEXT),
                          Update(t1, ITask(Interaction.NEXT), ip + 1, ip),
                          Update(t2, ITask(Interaction.PREV), ip + 2, ip + 1),
                          Guard({UnaryPredicateTerm(UnaryPredicate.ISTERMINATED, Read(CRef(t1))): ip + 3,
                                 UnaryPredicateTerm(UnaryPredicate.ISTERMINATED, Read(CRef(t2))): ip}, ip + 3),
                          Update(t1, CNone(), ip + 4, ip),
                          Update(t2, CNone(), ip + 5, ip),
                         ])

        s0 = self.initialize_machine(p, 2)
        s0.task_states[0].stack[0][0] = VNone.instance
        s0.task_states[0].stack[0][1] = VNone.instance
        lts, states, internal, external = self.explore(p, s0)

        print(lts2str(lts))

        self.assertEqual(7, len(states))
        self.assertEqual(9, len(external))
        self.assertEqual(4, len(internal))

    def test_CInt(self):
        """
        Tests the successful evaluation of CInt terms.
        """

        p = StackProgram([Update(FrameReference(0), CInt(42), 1, 1)])
        _, states, internal, external = self.explore(p, self.initialize_machine(p, 1))

        result = states[-1].content.task_states[0].stack[0][0]

        self.assertEqual(42, int(result))

    def test_CFloat(self):
        """
        Tests the successful evaluation of CFloat terms.
        """

        p = StackProgram([Update(FrameReference(0), CFloat(3.1415926), 1, 1)])
        _, states, internal, external = self.explore(p, self.initialize_machine(p, 1))

        result = states[-1].content.task_states[0].stack[0][0]

        self.assertEqual(3.1415926, float(result))

    def test_CBool(self):
        """
        Tests the successful evaluation of CFloat terms.
        """

        p = StackProgram([Update(FrameReference(0), CBool(False), 1, 1)])
        _, states, internal, external = self.explore(p, self.initialize_machine(p, 1))

        result = states[-1].content.task_states[0].stack[0][0]

        self.assertEqual(False, float(result))

    def test_CNone(self):
        """
        Tests the successful evaluation of CFloat terms.
        """

        p = StackProgram([Update(FrameReference(0), CNone(), 1, 1)])
        _, states, internal, external = self.explore(p, self.initialize_machine(p, 1))

        result = states[-1].content.task_states[0].stack[0][0]

        self.assertIs(VNone.instance, result)

    def test_CString(self):
        """
        Tests the successful evaluation of CFloat terms.
        """

        p = StackProgram([Update(FrameReference(0), CString("Hello World"), 1, 1)])
        _, states, internal, external = self.explore(p, self.initialize_machine(p, 1))

        result = states[-1].content.task_states[0].stack[0][0]

        self.assertEqual("Hello World", str(result))

    def test_ArithmeticUnaryOperation(self):

        """
        Tests the successful evaluation of ArithmeticUnaryOperation terms.
        """

        cases = [(ArithmeticUnaryOperation(ArithmeticUnaryOperator.MINUS, CInt(42)), VInt(-42)),
                 (ArithmeticUnaryOperation(ArithmeticUnaryOperator.NOT, CInt(42)), VInt(~42)),
                 (ArithmeticUnaryOperation(ArithmeticUnaryOperator.MINUS, CFloat(42.0)), VFloat(-42.0))]

        for term, value in cases:
            with self.subTest(term=term):
                p = StackProgram([Update(FrameReference(0), term, 1, 1)])
                _, states, _, _ = self.explore(p, self.initialize_machine(p, 1))
                result = states[-1].content.task_states[0].stack[0][0]
                self.assertEqual(value, result)

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

        for term, value in cases:
            with self.subTest(term=term):
                p = StackProgram([Update(FrameReference(0), term, 1, 1)])
                _, states, _, _ = self.explore(p, self.initialize_machine(p, 1))
                result = states[-1].content.task_states[0].stack[0][0]
                self.assertEqual(value, result)

    def test_BooleanBinaryOperation(self):

        """
        Tests the successful evaluation of BooleanBinaryOperation terms.
        """

        cases = [(BooleanBinaryOperation(BooleanBinaryOperator.AND, CBool(False), CBool(False)), VBool.false),
                 (BooleanBinaryOperation(BooleanBinaryOperator.AND, CBool(False), CBool(True)), VBool.false),
                 (BooleanBinaryOperation(BooleanBinaryOperator.AND, CBool(True), CBool(False)), VBool.false),
                 (BooleanBinaryOperation(BooleanBinaryOperator.AND, CBool(True), CBool(True)), VBool.true),
                 (BooleanBinaryOperation(BooleanBinaryOperator.OR, CBool(False), CBool(False)), VBool.false),
                 (BooleanBinaryOperation(BooleanBinaryOperator.OR, CBool(False), CBool(True)), VBool.true),
                 (BooleanBinaryOperation(BooleanBinaryOperator.OR, CBool(True), CBool(False)), VBool.true),
                 (BooleanBinaryOperation(BooleanBinaryOperator.OR, CBool(True), CBool(True)), VBool.true)
                 ]

        for term, value in cases:
            with self.subTest(term=term):
                p = StackProgram([Update(FrameReference(0), term, 1, 1)])
                _, states, _, _ = self.explore(p, self.initialize_machine(p, 1))
                result = states[-1].content.task_states[0].stack[0][0]
                self.assertEqual(value, result)

    def test_Comparison(self):

        """
        Tests the successful evaluation of Comparison terms.
        """

        cases = [(Comparison(ComparisonOperator.EQ, CInt(42), CFloat(42.0)), VBool.true),
                 (Comparison(ComparisonOperator.EQ, CInt(42), CFloat(43.0)), VBool.false),
                 (Comparison(ComparisonOperator.NEQ, CInt(42), CFloat(42.0)), VBool.false),
                 (Comparison(ComparisonOperator.NEQ, CInt(42), CFloat(43.0)), VBool.true),
                 (Comparison(ComparisonOperator.LESS, CInt(42), CFloat(374895.0)), VBool.true),
                 (Comparison(ComparisonOperator.LESS, CInt(42), CFloat(-43.0)), VBool.false),
                 (Comparison(ComparisonOperator.LESSOREQUAL, CInt(42), CInt(42)), VBool.true),
                 (Comparison(ComparisonOperator.LESSOREQUAL, CInt(42), CFloat(-43.0)), VBool.false),
                 (Comparison(ComparisonOperator.GREATER, CInt(42), CFloat(374895.0)), VBool.false),
                 (Comparison(ComparisonOperator.GREATER, CInt(42), CFloat(-43.0)), VBool.true),
                 (Comparison(ComparisonOperator.GREATEROREQUAL, CInt(42), CInt(42)), VBool.true),
                 (Comparison(ComparisonOperator.GREATEROREQUAL, CFloat(-43.0), CInt(42)), VBool.false),
                 (Comparison(ComparisonOperator.IS, CNone(), CNone()), VBool.true),
                 (Comparison(ComparisonOperator.IS, CInt(42), CNone()), VBool.false),
                 (Comparison(ComparisonOperator.ISNOT, CNone(), CNone()), VBool.false),
                 (Comparison(ComparisonOperator.ISNOT, CInt(42), CNone()), VBool.true),
                 (Comparison(ComparisonOperator.IN, CString("a"), CString("Hallo")), VBool.true),
                 (Comparison(ComparisonOperator.IN, CString("a"), CString("Hello")), VBool.false),
                 (Comparison(ComparisonOperator.NOTIN, CString("a"), CString("Hallo")), VBool.false),
                 (Comparison(ComparisonOperator.NOTIN, CString("a"), CString("Hello")), VBool.true)
                 ]

        for term, value in cases:
            with self.subTest(term=term):
                p = StackProgram([Update(FrameReference(0), term, 1, 1)])
                _, states, _, _ = self.explore(p, self.initialize_machine(p, 1))
                result = states[-1].content.task_states[0].stack[0][0]
                self.assertEqual(value, result)

    def test_UnaryPredicateTerm(self):

        """
        Tests the successful evaluation of UnaryPredicateTerm terms.
        """

        cases = [(UnaryPredicateTerm(UnaryPredicate.ISTERMINATED, ITask(Interaction.NEXT)), VBool.false),
                 (UnaryPredicateTerm(UnaryPredicate.ISCALLABLE, CInt(42)), VBool.false),
                 (UnaryPredicateTerm(UnaryPredicate.ISCALLABLE, Read(CRef(FrameReference(0)))), VBool.true),
                 (UnaryPredicateTerm(UnaryPredicate.ISEXCEPTION, CInt(42)), VBool.false),
                 (UnaryPredicateTerm(UnaryPredicate.ISEXCEPTION, NewTypeError("Just for testing.")), VBool.true)
                 ]

        for term, value in cases:
            with self.subTest(term=term):
                p = StackProgram([Update(FrameReference(0), term, 1, 1)])
                s0 = self.initialize_machine(p, 1)
                s0.task_states[0].stack[0][0] = VList.append
                _, states, _, _ = self.explore(p, s0)
                result = states[-1].content.task_states[0].stack[0][0]
                self.assertEqual(value, result)

    def test_IsInstance(self):
        """
        Tests the successful evaluation of IsInstance terms.
        """

        cases = [(IsInstance(CInt(42), NewTuple(CType(TBuiltin.float), CType(TBuiltin.int))), VBool.true),
                 (IsInstance(CInt(42), CType(TBuiltin.float)), VBool.false)
                 ]

        for term, value in cases:
            with self.subTest(term=term):
                p = StackProgram([Update(FrameReference(0), term, 1, 1)])
                _, states, _, _ = self.explore(p, self.initialize_machine(p, 1))
                result = states[-1].content.task_states[0].stack[0][0]
                self.assertEqual(value, result)

    def test_Read(self):
        """
        Tests the successful evaluation of Read terms.
        """

        cases = [(Read(CRef(FrameReference(0))), VInt(42))]

        for term, value in cases:
            with self.subTest(term=term):
                p = StackProgram([Update(FrameReference(0), term, 1, 1)])
                s0 = self.initialize_machine(p, 1)
                s0.task_states[0].stack[0][0] = VInt(42)
                _, states, _, _ = self.explore(p, s0)
                result = states[-1].content.task_states[0].stack[0][0]
                self.assertEqual(value, result)

    def test_new(self):
        """
        Tests the successful evaluation of terms that create new objects.
        """

        cases = [(NewTuple(CInt(42), CInt(4711)), VTuple(VInt(42), VInt(4711))),
                 (IsInstance(NewList(), CType(TBuiltin.list)), VBool.true),
                 (IsInstance(NewDict(), CType(TBuiltin.dict)), VBool.true),
                 (IsInstance(NewJumpError(VReturnError), CType(TBuiltin.return_error)), VBool.true),
                 (IsInstance(NewJumpError(VBreakError), CType(TBuiltin.break_error)), VBool.true),
                 (IsInstance(NewTypeError("Just a test."), CType(TBuiltin.type_error)), VBool.true)
                 ]

        for term, value in cases:
            with self.subTest(term=term):
                p = StackProgram([Update(FrameReference(0), term, 1, 1)])
                _, states, _, _ = self.explore(p, self.initialize_machine(p, 1))
                result = states[-1].content.task_states[0].stack[0][0]
                self.assertEqual(value, result)

    def test_namespace(self):
        """
        Tests the successful evaluation of namespace-related terms.
        """

        cases = [(IsInstance(NewNamespace(), CType(TBuiltin.namespace)), VBool.true),
                 (Lookup(Read(CRef(FrameReference(0))), CString("hello")), VInt(42))]

        for term, value in cases:
            with self.subTest(term=term):
                p = StackProgram([Update(FrameReference(0), term, 1, 1)])
                s0 = self.initialize_machine(p, 1)

                ns = VNamespace()
                ns[VStr("hello")] = VInt(42)

                s0.task_states[0].stack[0][0] = ns
                _, states, _, _ = self.explore(p, s0)
                result = states[-1].content.task_states[0].stack[0][0]
                self.assertEqual(value, result)

    def test_procedure(self):
        """
        Tests the successful evaluation of procedure-related terms.
        """

        q = StackProgram([Update(ReturnValueReference(),
                                               ArithmeticBinaryOperation(ArithmeticBinaryOperator.PLUS,
                                                                         Read(CRef(FrameReference(0))), CInt(1)), 1, 1),
                                        Pop()])

        p = StackProgram([Update(FrameReference(0), NewProcedure(1, q), 1, 3),
                          Push(Read(CRef(FrameReference(0))), [CInt(42)], 2, 3),
                          Update(FrameReference(0), NumArgs(Read(CRef(FrameReference(0)))), 3, 3)])

        state0 = self.initialize_machine(p, 1)

        _, states, internal, external = self.explore(p, state0)

        self.assertEqual(len(states), 2)
        self.assertEqual(len(internal), 1)
        self.assertEqual(len(external), 3)

        self.assertEqual(int(states[-1].content.task_states[0].returned), 43)
        self.assertEqual(int(states[-1].content.task_states[0].stack[0][0]), 1)

    def test_class(self):
        """
        Tests the successful evaluation of class-related terms.
        """

        # TODO: NewProperty, NewClass

    def test_LoadAttrCase(self):
        """
        Tests the successful evaluation of LoadAttrCase terms.
        """
        # TODO: LoadAttrCase

    def test_StoreAttrCase(self):
        """
        Tests the successful evaluation of StoreAttrCase terms.
        """
        # TODO: StoreAttrCase

    def test_module(self):
        """
        Tests the successful evaluation of module-related terms.
        """

        # TODO: Newmodule




