import unittest

from engine.exploration import explore, state_space, schedule_nonzeno
from engine.machine import MachineState
from engine.task import TaskStatus
from engine.tasks.instructions import StackProgram, ProgramLocation
from engine.tasks.interaction import InteractionState, Interaction
from engine.tasks.stack import StackState, Frame


class TestSpektakelMachine(unittest.TestCase):
    """
    This class is for testing Spektakelpy's virtual machine.
    """

    def initialize_machine(self, p):
        """
        Constructs the default initial state of the virtual machine.
        :param p: The StackProgram that should be executed by the machine.
        :return: A MachineState object.
        """

        frames = [Frame(ProgramLocation(p, 0), [])]

        m = StackState(0, TaskStatus.RUNNING, frames)

        isymbols = [Interaction.NEXT, Interaction.PREV, Interaction.TICK]
        istates = (InteractionState(i, iidx + 1) for iidx, i in enumerate(isymbols))

        return MachineState([m, *istates])

    def explore(self, p):
        """
        Computes the state space of the default machine for the given StackProgram.
        :param p: The StackProgram for which to explore the state space.
        :return: A tuple (lts, states, internal, external), where lts is an LTS, and states contains all the states
                 of this LTS, whereas 'internal' and 'external' contain all the internal transitions and interaction
                 transitions respectively.
        """

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

    # TODO: Test Update instruction
    # TODO: Test Guard instruction
    # TODO: Test Push instruction
    # TODO: Test Pop instruction
    # TODO: Test Launch instruction
    # TODO: Test InteractionState!
    # TODO: Test IntrinsicProcedure
    # TODO: Test CInt, CFloat, CBool, CNone, CString, ArithmeticUnaryOperation, ArithmeticBinaryOperation, BooleanBinaryOperation, Comparison, UnaryPredicateTerm, IsInstance, Read, Project, Lookup, LoadAttrCase, StoreAttrCase, NewTuple, NewDict, NewJumpException, NewTypeError, NewNameSpace, NewProcedure, NumArgs, NewProperty, NewClass, NewModule




