import io
import unittest
from io import StringIO

from engine.exploration import explore, state_space, schedule_nonzeno
from engine.functional.values import VNone
from engine.machine import MachineState
from engine.task import TaskStatus
from engine.tasks.program import ProgramLocation
from engine.tasks.interaction import InteractionState, Interaction
from engine.tasks.stack import StackState, Frame
from lang.spek import syntax, static, modules
from lang.spek.dynamic import Spektakel2Stack
from lang.spek.modules import SpekStringModuleSpecification
from tests.tools import dedent


class TestSpektakelTranslation(unittest.TestCase):
    """
    This class is for testing the translation from high-level Spektakel code into low-level VM code.
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

        isymbols = [Interaction.NEXT, Interaction.PREV, Interaction.TICK, Interaction.NEVER]
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

    def translate_explore(self, sample, roots=None):
        """
        Translates and executes the given code sample.
        :exception ParserError: If the given string was not a syntactically correct Spektakel program.
        :param sample: The code to lex, parse and validate, as a string.
        :param roots: The file system roots that should be searched for modules to be imported.
        :return: A tuple (node, env, dec, err), where node is the AST representing the code, env is an environment mapping
                 names to their declarations, dec is a mapping of refering nodes to their referents and err is an iterable
                 of ValidationErrors.
        """
        finder, builtin = modules.build_default_finder([] if roots is None else roots)
        v = static.SpektakelValidator(finder, builtin)

        translator = Spektakel2Stack(builtin)

        program = translator.translate(SpekStringModuleSpecification(sample, v, builtin))
        program = program.compile()

        _, states, internal, external = self.explore(program, self.initialize_machine(program, 2))

        return states, internal, external

    def test_empty(self):
        """
        Tests if the empty program is executed successfully.
        """

        states, internal, external = self.translate_explore("# Just some empty program.")

        self.assertEqual(len(states), 2)
        self.assertEqual(len(internal), 1)
        self.assertEqual(len(external), 3)

        for s in states:
            for t in s.content.task_states:
                if isinstance(t, StackState):
                    self.assertTrue(t.exception is None or isinstance(t.exception, VNone))

    def test_assignment_simple(self):
        """
        Tests the translation of simple assignment statements. This is useful for all future test cases.
        """
        program = """
        from interaction import never
        var x = 42
        var y = 4711
        x = x + 1
        y = x + y
        await never()
        """
        program = dedent(program)
        states, internal, external = self.translate_explore(program)

        self.assertEqual(len(states), 2)
        self.assertEqual(len(internal), 1)
        self.assertEqual(len(external), 3)

        for s in states:
            for t in s.content.task_states:
                if isinstance(t, StackState):
                    self.assertTrue(t.exception is None or isinstance(t.exception, VNone))

        self.assertEqual(int(states[-1].content.task_states[0].stack[-1][-1]), 4754)
