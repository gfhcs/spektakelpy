import unittest

from engine.exploration import explore, state_space, schedule_nonzeno
from engine.functional.reference import FrameReference, ReturnValueReference
from engine.functional.terms import CInt, CBool, ArithmeticBinaryOperation, ArithmeticBinaryOperator, Read, CRef
from engine.functional.values import VNone, VProcedure
from engine.machine import MachineState
from engine.task import TaskStatus
from engine.tasks.instructions import StackProgram, ProgramLocation, Update, Pop, Guard, Push, Launch
from engine.tasks.interaction import InteractionState, Interaction
from engine.tasks.stack import StackState, Frame


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

        m = StackState(0, TaskStatus.RUNNING, frames)

        isymbols = [Interaction.NEXT, Interaction.PREV, Interaction.TICK]
        istates = (InteractionState(i, iidx + 1) for iidx, i in enumerate(isymbols))

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
                    if isinstance(s.content.get_task_state(t.label), InteractionState):
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
        Tests the execution of Update instructions.
        """

        p = StackProgram([Update(FrameReference(0), CInt(42), 1, 1),
                          Guard({}, 1)])
        _, states, internal, external = self.explore(p, self.initialize_machine(p, 1))

        self.assertEqual(len(states), 2)
        self.assertEqual(len(internal), 1)
        self.assertEqual(len(external), 3)

        self.assertEqual(int(states[1].content.get_task_state(0).stack[0][0]), 42)
        self.assertIs(states[1].content.get_task_state(0).exception, None)

    def test_update_failure(self):
        p = StackProgram([Update(FrameReference(1), CInt(42), 1, 1),
                          Guard({}, 1)])
        _, states, internal, external = self.explore(p, self.initialize_machine(p, 1))

        self.assertEqual(len(states), 2)
        self.assertEqual(len(internal), 1)

        self.assertEqual(states[1].content.get_task_state(0).stack[0][0], VNone.instance)
        self.assertIsNot(states[1].content.get_task_state(0).exception, None)

    def test_guard_success(self):
        """
        Tests the execution of Guard instructions.
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
        false = CBool(False)
        true = CBool(True)

        p = StackProgram([Guard({false: 1, true: 34634}, 1),
                          Guard({}, 1)])
        _, states, internal, external = self.explore(p, self.initialize_machine(p))

        self.assertEqual(len(states), 2)
        self.assertEqual(len(internal), 1)
        self.assertEqual(len(external), 3)

        self.assertIsNot(states[1].content.get_task_state(0).exception, None)

    def test_pop_success(self):
        """
        Tests the execution of Update instructions.
        """

        p = StackProgram([Pop()])
        _, states, internal, external = self.explore(p, self.initialize_machine(p, 1))

        self.assertEqual(len(states), 2)
        self.assertEqual(len(internal), 1)
        self.assertEqual(len(external), 3)

        self.assertEqual(len(states[0].content.get_task_state(0).stack), 1)
        self.assertEqual(len(states[1].content.get_task_state(0).stack), 0)

    def test_pop_failure(self):
        p = StackProgram([Pop(), Pop()])
        _, states, internal, external = self.explore(p, self.initialize_machine(p))

        self.assertEqual(len(states), 2)
        self.assertEqual(len(internal), 1)

        self.assertEqual(len(states[0].content.get_task_state(0).stack), 1)
        self.assertEqual(len(states[1].content.get_task_state(0).stack), 0)

    def test_push_success(self):
        """
        Tests the execution of Update instructions.
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

        self.assertEqual(int(states[1].content.get_task_state(0).returned), 43)
        self.assertIs(states[1].content.get_task_state(0).exception, None)

    def test_push_failure(self):

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

        self.assertIsNot(states[1].content.get_task_state(0).exception, None)

    def test_launch_success(self):
        """
        Tests the execution of Update instructions.
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

        self.assertIsNot(states[1].content.get_task_state(0).returned, None)
        tid = int(states[1].content.get_task_state(0).returned)
        self.assertEqual(int(states[2].content.get_task_state(tid).returned), 43)

    def test_launch_failure(self):

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

        self.assertIsNot(states[1].content.get_task_state(0).exception, None)


    # TODO: Test InteractionState!
    # TODO: Test IntrinsicProcedure
    # TODO: Test CInt, CFloat, CBool, CNone, CString, ArithmeticUnaryOperation, ArithmeticBinaryOperation, BooleanBinaryOperation, Comparison, UnaryPredicateTerm, IsInstance, Read, Project, Lookup, LoadAttrCase, StoreAttrCase, NewTuple, NewDict, NewJumpException, NewTypeError, NewNameSpace, NewProcedure, NumArgs, NewProperty, NewClass, NewModule




