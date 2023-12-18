import unittest

from engine.exploration import explore, state_space, schedule_nonzeno
from engine.functional.values import VNone
from engine.machine import MachineState
from engine.task import TaskStatus
from engine.tasks.interaction import InteractionState, Interaction
from engine.tasks.program import ProgramLocation
from engine.tasks.stack import StackState, Frame
from lang.spek import static, modules
from lang.spek.dynamic import Spektakel2Stack
from lang.spek.modules import SpekStringModuleSpecification
from tests.samples_translation.expressions import samples as expressions
from tests.samples_translation.assignments import samples as assignments
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

    def examine_sample(self, code, num_states, num_internal, num_external, **expectation):
        """
        Translates and executes a code sample, in order to examine the final state.
        This procedure will make a test fail if the translation and execution of the code does not meet expectations.
        :param code: The string encoding the program to examine.
        :param num_states: The number of observable states for the program.
        :param num_internal: The number of observable internal transitions for the program.
        :param num_external: The number of observable external transitions for the program.
        :param expectation: A dict mapping variable names to expected values.
        """
        code = dedent(code)
        states, internal, external = self.translate_explore(code)

        self.assertEqual(len(states), num_states)
        self.assertEqual(len(internal), num_internal)
        self.assertEqual(len(external), num_external)

        for s in states:
            for t in s.content.task_states:
                if isinstance(t, StackState):
                    if not (t.exception is None or isinstance(t.exception, VNone)):
                        raise t.exception

        for vname, expected in expectation.items():
            found = states[-1].content.task_states[0].stack[-1][0][vname]
            if expected is None:
                self.assertTrue(isinstance(found, VNone))
            elif isinstance(expected, str):
                self.assertEqual(found.string, expected)
            else:
                self.assertEqual((type(expected))(found), expected)

    def examine_samples(self, samples):
        """
        Translates and executes a set of samples and examines their final states.
        This procedure will make a test fail if the translation and execution of a sample does not meet expectations.
        :param samples: A dict that maps program strings to examination tuples. An examination tuple has the form
                        ((num_states, num_internal, num_external), expectation), where num_states is the number
                        of states observable for the program, num_internal and num_external are the numbers of internal
                        and external transitions and expectation is a dict mapping variable names to expected values.
        """
        for idx, (program, (numbers, expectation)) in enumerate(samples.items()):
            with self.subTest(idx=idx):
                self.examine_sample(program, *numbers, **expectation)

    def test_empty(self):
        """
        Tests if the empty program is executed successfully.
        """
        self.examine_sample("# Just some empty program.", 2, 1, 3)

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

        self.examine_sample(program, 2, 1, 3, y=4754)

    def test_expressions(self):
        """
        Tests the translation of all expression types, by executing the translation result and inspecting the final
        machine state.
        """
        self.examine_samples(expressions)

    def test_pass(self):
        """
        Tests the 'pass' statement.
        """
        program = """
        pass
        pass
        pass
        """

        self.examine_sample(program, 2, 1, 3)

    def test_assignments(self):
        """
        Tests more complex assignments, in particular assignments to patterns.
        """
        self.examine_samples(assignments)

    def test_if(self):
        """
        Tests if statements, including elif and else clauses.
        """
        raise NotImplementedError()

    def test_while(self):
        """
        Tests while loops, including break and continue.
        """
        raise NotImplementedError()

    def test_procedures(self):
        """
        Tests the definition and execution of procedures, involving Call expressions, Return statements and recursion.
        """
        raise NotImplementedError()

    def test_async(self):
        """
        Tests launching and awaiting procedures as tasks, involving Launch and Await expressions.
        """
        raise NotImplementedError()

    def test_exceptions(self):
        """
        Test creation, raising and handling of exceptions, i.e. the constructors of exception types, Raise statements,
        and try blocks.
        """
        # TODO: Insbesondere will ich für das finally folgende Fälle abtesten:
        #         If an exception occurs during execution of the try clause, the exception may be handled by an except clause. If the exception is not handled by an except clause, the exception is re-raised after the finally clause has been executed.
        #         An exception could occur during execution of an except or else clause. Again, the exception is re-raised after the finally clause has been executed.
        #         If the finally clause executes a break, continue or return statement, exceptions are not re-raised.
        #         If the try statement reaches a break, continue or return statement, the finally clause will execute just prior to the break, continue or return statement’s execution.
        #         If a finally clause includes a return statement, the returned value will be the one from the finally clause’s return statement, not the value from the try clause’s return statement.
        #         --> Insbesondere müssen Nester aus Schleifen und (mehreren) Finallys getestet werden.
        raise NotImplementedError()

    def test_for(self):
        """
        Tests for loops, including break and continue.
        """
        raise NotImplementedError()

    def test_tuples(self):
        """
        Tests the creation and usage of tuples, including Projection expressions and "in" expressions
        """
        raise NotImplementedError()

    def test_lists(self):
        """
        Tests the creation and usage of lists, including Projection expressions and "in" expressions,
        assignment to projection expressions.
        """
        raise NotImplementedError()

    def test_dicts(self):
        """
        Tests the creation and usage of dicts, including Projection expressions and "in" expressions, including
        assignment to projection expressions.
        """
        raise NotImplementedError()

    def test_classes(self):
        """
        Tests the creation and instantiation of classes, including inheritance and defining/calling methods.
        """
        raise NotImplementedError()

    def test_properties(self):
        """
        Tests the declaration and execution of properties, involving attribute expressions, assignment to attribute expressions.
        """
        raise NotImplementedError()

    def test_imports(self):
        """
        Tests the execution of import statements.
        """
        raise NotImplementedError()
