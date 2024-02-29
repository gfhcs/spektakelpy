import unittest

from engine.exploration import explore, schedule_nonzeno
from engine.functional.values import VNone, VCell, VException, VCancellationError
from engine.machine import MachineState
from engine.task import TaskStatus
from engine.tasks import interaction
from engine.tasks.interaction import InteractionState, Interaction, num_interactions_possible, i2s
from engine.tasks.program import ProgramLocation
from engine.tasks.stack import StackState, Frame
from lang.spek import static, modules
from lang.spek.dynamic import Spektakel2Stack
from lang.spek.modules import SpekStringModuleSpecification
from state_space.equivalence import bisimilar, reach_wbisim
from state_space.lts import state_space, Transition, State, LTS
from tests.samples_translation.assignments import samples as assignments
from tests.samples_translation.choice import code as code_choice
from tests.samples_translation.closures import samples as closures
from tests.samples_translation.diamond import code as code_diamond
from tests.samples_translation.expressions import samples as expressions
from tests.samples_translation.future_equality import code as code_future_equality
from tests.samples_translation.ifs import samples as ifs
from tests.samples_translation.manboy import code as code_manboy
from tests.samples_translation.philosophers_deadlock import code as code_philosophers_deadlock
from tests.samples_translation.procedures import samples as procedures
from tests.samples_translation.producer_consumer import code as code_producer_consumer
from tests.samples_translation.tasks import samples as tasks
from tests.samples_translation.turns import code as code_turns
from tests.samples_translation.twofirecracker import code as code_twofirecracker
from tests.samples_translation.whiles import samples as whiles
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
        return MachineState([m, *(InteractionState(i) for i in Interaction)])

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

    def translate_explore(self, sample, roots=None):
        """
        Translates and executes the given code sample.
        :exception ParserError: If the given string was not a syntactically correct Spektakel program.
        :param sample: The code to lex, parse and validate, as a string.
        :param roots: The file system roots that should be searched for modules to be imported.
        :return: A return value from self.explore.
        """
        finder, builtin = modules.build_default_finder([] if roots is None else roots)
        v = static.SpektakelValidator(finder, builtin)

        translator = Spektakel2Stack(builtin)

        program = translator.translate(SpekStringModuleSpecification(sample, v, builtin))
        program = program.compile()

        return self.explore(program, self.initialize_machine(program, 2))

    def examine_sample(self, code, num_states, num_internal, num_external, bisim=None, project=None, **expectation):
        """
        Translates and executes a code sample, in order to examine the final state.
        This procedure will make a test fail if the translation and execution of the code does not meet expectations.
        :param code: The string encoding the program to examine.
        :param num_states: The number of observable states for the program.
        :param num_internal: The number of observable internal transitions for the program.
        :param num_external: The number of observable external transitions for the program.
        :param bisim: If an LTS is given there, the preprocessed state space of the sample will be checked for weak
                      bisimilarity to that LTS. Preprocessing does the following:
                      1. All state content will be projected to the value of one global variable.
                      2. Interaction transition labels will be set to the string names of the respective interaction.
                      3. All internal transitions will be eliminated, by discarding the transition itself and replacing
                         the start state of each such transition by its end state. This operation is repeated until
                         no internal transitions remain.

                      Step 3 works because a state that has internal transitions enabled can only have exactly one
                      such transition enabled. Step 3 is necessary because external interactions do not change
                      (projected) state instantaneously and a number of internal transitions is required after the
                      interaction in order to update the internal state. In order for bisimulation to work out, though,
                      the state labels would have to be changed immediately, which we achieve by step 3.
        :param project: A procedure that takes VM states and maps them to LTS state labels, which are taken into account
                        when checking for bisimilarity. If this value is omitted, all state content will simply be discarded.
        :param expectation: A dict mapping variable names to expected values.
        """
        code = dedent(code)
        sp, states, internal, external = self.translate_explore(code)

        # print(lts2dot(sp))

        for s in states:
            for t in s.content.task_states:
                if isinstance(t, StackState):
                    if not (t.exception is None or isinstance(t.exception, (VNone, VCancellationError))):
                        if isinstance(t.exception, VException) and t.exception.pexception is not None:
                            raise t.exception.pexception
                        else:
                            raise t.exception

        if num_states is not None:
            self.assertEqual(len(states), num_states)
        if num_internal is not None:
            self.assertEqual(len(internal), num_internal)
        if num_external is not None:
            self.assertEqual(len(external), num_external)

        for vname, expected in expectation.items():
            found = states[-1].content.task_states[0].stack[-1][0][vname]
            if isinstance(found, VCell):
                found = found.value
            if expected is None:
                self.assertTrue(isinstance(found, VNone))
            elif isinstance(expected, str):
                self.assertEqual(found.string, expected)
            else:
                self.assertEqual((type(expected))(found), expected)

        if bisim is not None:

            if project is None:
                project = lambda s: None
            def p(s):
                return State(None if s.content is None else project(s.content))

            internal, external = (set(id(t) for t in ts) for ts in (internal, external))

            zeno = State(None).seal()

            def follow_taus(state):
                succ = state
                seen = set()
                while any(id(t) in internal for t in succ.transitions):
                    # We assume: If a state has an internal transition, then this transition is the *only* transition.
                    assert len(succ.transitions) == 1
                    if succ in seen:
                        return zeno
                    seen.add(succ)
                    succ = succ.transitions[0].target
                return succ

            initial = follow_taus(sp.initial)
            agenda = [initial]
            s2p = {initial: (p(initial), False)}

            while len(agenda) > 0:
                s = agenda.pop()

                ss, done = s2p[s]

                if done:
                    continue

                s2p[s] = (ss, True)

                # Any proper state that makes it into the agenda must not have any internal transitions:
                assert not any(id(t) in internal for t in s.transitions)

                # Now look at all successor states and replace them by their tau chain ends:
                for t in s.transitions:
                    # Turn the external transition followed by the tau chain into one simple transition:
                    target = follow_taus(t.target)
                    try:
                        sss, sdone = s2p[target]
                    except KeyError:
                        sss = p(target)
                        s2p[target] = (sss, False)
                        sdone = False

                    task = s.content.task_states[t.label]
                    assert isinstance(task, InteractionState)
                    ss.add_transition(Transition(interaction.i2s(task.interaction), sss))
                    if not sdone:
                        agenda.append(target)

            sp_processed = LTS(s2p[initial][0].seal())

            # print("Expected:")
            # print(lts2dot(bisim))
            # print("Explored:")
            # print(lts2dot(sp_processed))

            self.assertTrue(bisimilar(reach_wbisim, sp_processed, bisim))

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
        self.examine_sample("# Just some empty program.", 2, 1, num_interactions_possible)

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

        self.examine_sample(program, 2, 1, num_interactions_possible, y=4754)

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

        self.examine_sample(program, 2, 1, num_interactions_possible)

    def test_assignments(self):
        """
        Tests more complex assignments, in particular assignments to patterns.
        """
        self.examine_samples(assignments)

    def test_if(self):
        """
        Tests if statements, including elif and else clauses.
        """
        self.examine_samples(ifs)

    def test_while(self):
        """
        Tests while loops, including break and continue.
        """
        self.examine_samples(whiles)

    def test_procedures(self):
        """
        Tests the definition and execution of procedures, involving:
            - call statements and call expressions (also nested deep inside expressions).
            - calls in if conditions and while heads.
            - return statements, also inside if statements and loops.
            - recursion and entangled recursion.
            - reassignment to procedure identifiers.
        """
        self.examine_samples(procedures)

    def test_manboy(self):
        """
        This is the Spek version of Donald Knuth's famous "Man or boy" test.
        """
        def manboy(k0=10):
            def a(k, x1, x2, x3, x4, x5):
                def b():
                    nonlocal k
                    k -= 1
                    return a(k, b, x1, x2, x3, x4)
                return x4() + x5() if k <= 0 else b()

            def one():
                return 1
            def minusone():
                return -1
            def zero():
                return 0

            return a(k0, one, minusone, minusone, one, zero)

        for k0 in range(10):
            expected = manboy(k0)
            with self.subTest(k0=k0, expected=expected):
                self.examine_sample(code_manboy.format(k0=k0), 2, 1, num_interactions_possible, result=expected)

    def test_closures(self):
        """
        This tests if procedures with free variables can properly be passed around as objects, even though some
        of the variables they use may already have been removed from the call stack. These test cases are more
        challenging that those in test_procedures.
        """
        self.examine_samples(closures)

    def test_async_success(self):
        """
        Tests launching and awaiting procedures as tasks, involving Launch and Await expressions. This should also
        include some infinite loops through a finite state space.
        """
        self.examine_samples(tasks)

    def test_async_diamond(self):
        """
        Tests if two counting tasks actually create a proper interleaving diamond. Also, this test case is an example
        of an infinite computation in a finite state space.
        """

        # Actually, based on sketching out the state space on paper, I would expect 15 states, 11 internal transitions
        # and 12 external transitions.
        # However, the state space turns out to be considerably larger. This might of course be due to a bug.
        # But just as well it can be explained by the code generation allocating local variables, such as for
        # the await expressions, that are 'None' in a first iteration will briefly be used and are then actually dead,
        # but nevertheless *keep* their new, now useless values, until they are written in a subsequent iteration.
        # This means: Code generation creates local variables with a short liveness period. These not only make states
        # themselves larger, but also prevent states from comparing equal, because these variables retain different
        # values while they are not live anymore. We should NOT fix this problem in code generation, because that
        # would be difficult to program, make the translation code a lot more complex and at the end of the day would
        # not anyway not catch all cases of such variables. Instead, one should implement a combination of
        # SCCP and liveness analysis, on the basis of SSA form. Getting out of SSA during register allocation would
        # then make sure that we use a minimal number of local variables, reusing dead stack frame slots, or at least
        # overwriting them with None.
        # Since we did not want to open the can labelled "Static analysis and transformation" at an early stage of
        # development (i.e. before event the language translation was fully tested for correctness, and thus
        # before we could verify that this problem even has a significant impact in practise), we have started to use
        # bisimilarity tests here, which, despite state spaces having hard-to-predict shapes, verify that *behavior*
        # is equivalent to what we expect.

        def interaction(s, sp, sn):
            s.add_transition(Transition("PREV", sp))
            s.add_transition(Transition("NEXT", sn))
            for i in Interaction:
                if i not in (Interaction.PREV, Interaction.NEXT, Interaction.NEVER):
                    s.add_transition(Transition(i2s(i), s))

        s0 = State(0)
        s1 = State(10)
        s2 = State(1)
        s3 = State(11)
        interaction(s0, s1, s2)
        interaction(s1, s0, s3)
        interaction(s2, s3, s0)
        interaction(s3, s2, s1)
        reduced = LTS(s0.seal())

        def p(state):
            return int(state.task_states[0].stack[-1][0]['state'].value)

        self.examine_sample(code_diamond, None, None, None, bisim=reduced, project=p)

    def test_async_producer_consumer(self):
        """
        Test a simple producer-consumer setup. This sample only works if concurrency is available.
        """

        def edges(s, *es):
            noloop = {Interaction.NEVER}
            for i, target in zip(es[::2], es[1::2]):
                s.add_transition(Transition(i2s(i), target))
                noloop.add(i)
            for j in Interaction:
                if j not in noloop:
                    s.add_transition(Transition(i2s(j), s))

        # This is similar to the reduced state space produced by pseuco.com:
        s0, s1, s2, s3 = [State(consumed) for consumed in (0, 3, 32, 321)]
        edges(s0, Interaction.NEXT, s1)
        edges(s1, Interaction.NEXT, s2)
        edges(s2, Interaction.NEXT, s3)
        edges(s3)
        reduced = LTS(s0.seal())

        def p(state):

            tasks = [t for t in state.task_states if isinstance(t, StackState)]

            try:
                return int(tasks[0].stack[-1][0]['consumed'].value)
            except:
                raise

        self.examine_sample(code_producer_consumer, None, None, None, bisim=reduced, project=p)

    def test_async_pseuco_twofirecracker(self):
        """
        A spek implementation of the "TwoFireCracker" example from pseuco.com.
        The CCS code is:

            Match := strike?. MatchOnFire
            MatchOnFire := light!. MatchOnFire + extinguish!.0
            TwoFireCracker := light?. (bang!. 0 | bang!. 0)

            (Match | TwoFireCracker) \ {light} // this is the initial process

        """

        a2i = {"strike?": Interaction.NEXT,
               "bang!": Interaction.PREV,
               "extinguish!": Interaction.TICK,
               None: Interaction.RESUME}

        def edges(s, *es):
            noloop = {Interaction.NEVER}
            for action, target in zip(es[::2], es[1::2]):
                i = a2i[action]
                s.add_transition(Transition(i2s(i), target))
                noloop.add(i)
            for j in Interaction:
                if j not in noloop:
                    s.add_transition(Transition(i2s(j), s))

        # This is similar to the reduced state space produced by pseuco.com:
        s0, s1, s2, s3, s4, s5, s6, s7 = [State(idx) for idx in range(8)]
        edges(s0, "strike?", s6)
        edges(s1, "extinguish!", s2)
        edges(s2)
        edges(s3, "bang!", s1, "extinguish!", s5)
        edges(s4, "bang!", s5)
        edges(s5, "bang!", s2)
        edges(s6, None, s7, "extinguish!", s2)
        edges(s7, "extinguish!", s4, "bang!", s3)
        reduced = LTS(s0.seal())

        def p(state):
            return int(state.task_states[0].stack[-1][0]['state'].value)

        self.examine_sample(code_twofirecracker, None, None, None, bisim=reduced, project=p)

    def test_future_equality(self):
        """
        A simple test to make sure that futures are NOT considered equal just because of their content.
        """

        def edges(s, *es):
            noloop = {Interaction.NEVER}
            for i, target in zip(es[::2], es[1::2]):
                s.add_transition(Transition(i2s(i), target))
                noloop.add(i)
            for j in Interaction:
                if j not in noloop:
                    s.add_transition(Transition(i2s(j), s))

        s0, s1, s2, s3 = State((False, False, False, True)), State((False, False, True, False)), State((False, True, False, False)), State((True, False, False, False))
        edges(s0, Interaction.TICK, s1)
        edges(s1, Interaction.TICK, s2)
        edges(s2, Interaction.TICK, s3)
        edges(s3)
        reduced = LTS(s0.seal())

        def p(state):
            v, w, x, y, z = (state.task_states[0].stack[-1][0][v] for v in "vwxyz")
            return v is w, w is x, x is y, y is z

        self.examine_sample(code_future_equality, None, None, None, bisim=reduced, project=p)

    def test_async_turns(self):
        """
        Two players taking turns nondeterministically. This is a reduced variant of the dining philosophers, aimed
        at studying certain bugs more easily.
        """

        def edges(s, *es):
            noloop = {Interaction.NEVER}
            for i, target in zip(es[::2], es[1::2]):
                s.add_transition(Transition(i2s(i), target))
                noloop.add(i)
            for j in Interaction:
                if j not in noloop:
                    s.add_transition(Transition(i2s(j), s))

        ww, wp, pw = State((False, False)), State((False, True)), State((True, False))
        edges(ww, Interaction.NEXT, pw, Interaction.PREV, wp)
        edges(pw, Interaction.TICK, ww)
        edges(wp, Interaction.TICK, ww)
        reduced = LTS(ww.seal())

        def p(state):
            return tuple(bool(state.task_states[0].stack[-1][0][v].value) for v in ("s0", "s1"))

        self.examine_sample(code_turns, None, None, None, bisim=reduced, project=p)

    def test_async_choice(self):
        """
        Similar to test_async_turns, but nondeterministic choice is implemented differently, and both players are
        allowed to play at the same time.
        """

        def edges(s, *es):
            noloop = {Interaction.NEVER}
            for i, target in zip(es[::2], es[1::2]):
                s.add_transition(Transition(i2s(i), target))
                noloop.add(i)
            for j in Interaction:
                if j not in noloop:
                    s.add_transition(Transition(i2s(j), s))

        ww, wp, pw, pp = State((False, False)), State((False, True)), State((True, False)), State((True, True))
        edges(ww, Interaction.NEXT, pw, Interaction.PREV, wp)
        edges(pw, Interaction.NEXT, ww, Interaction.PREV, pp)
        edges(wp, Interaction.NEXT, pp, Interaction.PREV, ww)
        edges(pp, Interaction.NEXT, wp, Interaction.PREV, pw)
        reduced = LTS(ww.seal())

        def p(state):
            return tuple(bool(state.task_states[0].stack[-1][0][v].value) for v in ("s0", "s1"))

        self.examine_sample(code_choice, None, None, None, bisim=reduced, project=p)

    def test_async_philosophers_deadlock(self):
        """
        An implementation of the famous "Dining philosophers" problem: 3 philosophers pick up first the spoon to their
        left, then the spoon to their right. This can lead to deadlocks.
        """

        l2i = {0: Interaction.NEXT,
               1: Interaction.PREV,
               2: Interaction.RESUME,
               None: None}

        steps = ["", "awaiting_left", "has_left", "awaiting_right", "eating", "has_right"]

        def status2content(status):
            return " | ".join(steps[i] for i in status)

        status0 = (0, 0, 0)
        state0 = State(status2content(status0))
        agenda = [status0]
        status2state = {status0: (state0, False)}

        while len(agenda) > 0:
            status = agenda.pop()
            state, completed = status2state[status]
            if completed:
                continue

            status2state[status] = (state, True)

            for idx in range(3):
                step = status[idx]
                lbl = idx
                if step == 0:
                    if status[(idx - 1) % 3] in (0, 1, 2, 3):
                        step = 2
                    else:
                        step = 1
                elif step == 1:
                    if status[(idx - 1) % 3] in (0, 1, 2, 3):
                        lbl = None
                        step = 2
                elif step == 2:
                    if status[(idx + 1) % 3] in (0, 1, 5):
                        step = 4
                    else:
                        step = 3
                elif step == 3:
                    if status[(idx + 1) % 3] in (0, 1, 5):
                        lbl = None
                        step = 4
                elif step == 4:
                    step = 5
                elif step == 5:
                    step = 0

                status_target = [*status[:idx], step, *status[idx + 1:]]

                # At this stage, internal actions could replace the status before it can be observed:
                for jdx in range(3):
                    if status_target[jdx] == 1 and status_target[jdx - 1] not in (4, 5) \
                    or status_target[jdx] == 3 and status_target[(jdx + 1) % len(status_target)] not in (2, 3, 4):
                        status_target[jdx] += 1

                status_target = tuple(status_target)
                try:
                    target, _ = status2state[status_target]
                except KeyError:
                    target = State(status2content(status_target))
                    agenda.append(status_target)
                    status2state[status_target] = (target, False)

                i = l2i[lbl]
                state.add_transition(Transition(i2s(i), target))

        found_deadlock = False
        for state, _ in status2state.values():
            noloop = {i2s(Interaction.NEVER), *(t.label for t in state.transitions)}
            for j in Interaction:
                s = i2s(j)
                if s not in noloop:
                    state.add_transition(Transition(s, state))
            found_deadlock |= all(t.target is state for t in state.transitions)

        assert found_deadlock
        reduced = LTS(state0.seal())

        def p(state):
            def s2i(s):
                i = steps.index(s)
                assert i >= 0
                return i

            return status2content(tuple(s2i(str(state.task_states[0].stack[-1][0][f's{idx}'].value.string)) for idx in range(3)))

        self.examine_sample(code_philosophers_deadlock, None, None, None, bisim=reduced, project=p)

    def test_exceptions(self):
        """
        Test creation, raising and handling of exceptions, i.e. the constructors of exception types, Raise statements,
        and try blocks. These test samples also include exceptions and cance
        """
        # TODO: Insbesondere will ich für das finally folgende Fälle abtesten:
        #         If an exception occurs during execution of the try clause, the exception may be handled by an except clause. If the exception is not handled by an except clause, the exception is re-raised after the finally clause has been executed.
        #         An exception could occur during execution of an except or else clause. Again, the exception is re-raised after the finally clause has been executed.
        #         If the finally clause executes a break, continue or return statement, exceptions are not re-raised.
        #         If the try statement reaches a break, continue or return statement, the finally clause will execute just prior to the break, continue or return statement’s execution.
        #         If a finally clause includes a return statement, the returned value will be the one from the finally clause’s return statement, not the value from the try clause’s return statement.
        #         --> Insbesondere müssen Nester aus Schleifen und (mehreren) Finallys getestet werden.
        raise NotImplementedError()

    def test_async_failure(self):
        """
        Tests the exception handling and cancellation for tasks and futures.
        """
        # TODO: Futures can fail or be cancelled, which is a simple status change for them that should raise
        #       certain exceptions for all stakeholders of the future.
        # TODO: Tasks should, just like futures, also be able to raise exceptions or be cancelled!
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

    def test_for(self):
        """
        Tests for loops, including break and continue.
        """

        # TODO: Here and in many of the following test cases, we will have to use an object's interface.
        #       This cannot be done with terms only, because terms are functional, but many of the operations in
        #       question have side effects. So we must use instructions. The only useful instruction is
        #       the push instruction, which can be used to call double-underscore methods. Using them might make
        #       certain terms obsolete, which is good.
        #       The alternative would be to introduce additional instructions for the special methods, but this
        #       bloats the instruction set and does not really have any advantages.

        # TODO: Repeat all while test cases here.

        # TODO: Specifically test the allocation of the loop variable as a cell. See closure test cases for inspiration.

        raise NotImplementedError()

    def test_classes(self):
        """
        Tests the creation and instantiation of classes, including inheritance and defining/calling methods, as well
        as local types (i.e. types defined in scopes other than module level.
        """

        # TODO: Extend and use the samples in classes.py!

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

    def test_examples(self):
        """
        Tests the translator on all spek examples.
        """
        raise NotImplementedError()