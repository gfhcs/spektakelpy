import os.path
import unittest
from io import StringIO

from examples import paths as example_paths
from lang.spek import syntax, static, modules


def validate(sample, env=None, roots=None):
    """
    Lexes, parses and validates the given code sample.
    :param env: The environment in which the AST of the given sample is to be validated.
    :exception ParserError: If the given string was not a syntactically correct Spektakel program.
    :param sample: The code to lex, parse and validate, as a string.
    :param roots: The file system roots that should be searched for modules to be imported.
    :return: A tuple (node, env, dec, err), where node is the AST representing the code, env is an environment mapping
             names to their declarations, dec is a mapping of refering nodes to their referents and err is an iterable
             of ValidationErrors.
    """
    sample = StringIO(sample)
    lexer = syntax.SpektakelLexer(sample)
    node = syntax.SpektakelParser.parse_block(lexer)
    finder = modules.build_default_finder([] if roots is None else roots)
    v = static.SpektakelValidator(finder)
    return (node, *v.validate(node, env))


class TestSpektakelValidator(unittest.TestCase):

    def assertErrors(self, expected_count, err):
        """
        Asserts that the given number of errors was found and prints an informative error message if this is not the
        case.
        :param expected_count: The number of errors expected to be found.
        :param err: An iterable of the errors that were found.
        """

        msg = "Expected {} errors, but got {}:\n{}".format(expected_count,
                                                           len(err),
                                                           "\n".join((str(e) for e in err)))
        self.assertEqual(expected_count, len(err), msg=msg)

    def assertNoErrors(self, err):
        """
        Asserts that no errors were found, or prints an informative error message.
        :param err: The errors that were found.
        """
        return self.assertErrors(0, err)

    def test_empty(self):
        """
        Tests the validator on the AST of the empty program.
        """

        env_in = static.SpektakelValidator.environment_default()
        node, env_out, dec, err = validate("# Just some empty program.", env=env_in)

        self.assertEqual(len(env_in), len(env_out))
        self.assertEqual(len(dec), 0)
        self.assertNoErrors(err)

    def test_constants(self):
        """
        Tests the validator on all sorts of constants.
        """
        env_in = static.SpektakelValidator.environment_default()

        node, env_out, dec, err = validate("True\n"
                                       "False\n"
                                       "None\n"
                                       "\"Hello world!\"\n"
                                       "\"\"\"Hello world!\"\"\"\n"
                                       "42\n"
                                       "3.1415926\n", env_in)

        self.assertEqual(len(env_in), len(env_out))
        self.assertNoErrors(err)

        found = set(dec.values())
        expected = {True, False, None, "Hello world!", 42, 3.1415926}
        self.assertSetEqual(found, expected)

    def test_identifiers(self):
        """
        Tests the correct resolution of identifiers.
        """
        env_in = static.SpektakelValidator.environment_default()

        node, env_out, dec, err = validate("x\n"
                                           "var x\n"
                                           "x = x + 42\n"
                                           "var x\n"
                                           "def x(a, b):\n"
                                           "  return x(b, a)", env_in)

        self.assertEqual(len(env_out), len(env_in) + 1)
        self.assertErrors(1, err)
        self.assertEqual(7, len(dec))

    def test_pass(self):
        """
        Makes sure that pass statements don't crash the validator.
        """
        env_in = static.SpektakelValidator.environment_default()

        node, env_out, dec, err = validate("pass", env_in)

        self.assertEqual(len(env_in), len(env_out))
        self.assertNoErrors(err)

        self.assertSetEqual(set(), set(dec.values()))

    def test_expressions(self):
        """
        Tests the validation of some expressions
        """

        env_in = static.SpektakelValidator.environment_default()

        node, env_out, dec, err = validate("1 + 2\n"
                                           "var x = 42\n"
                                           "(await f(x)) + 42\n"
                                           "a and x > 5\n"
                                           "x.somefantasyname", env_in)

        self.assertEqual(len(env_out), len(env_in) + 1)
        self.assertErrors(2, err)
        self.assertEqual(8, len(dec))

    def test_assignment(self):
        """
        Tests the validation of assignments
        """

        env_in = static.SpektakelValidator.environment_default()

        node, env_out, dec, err = validate("var x, y, z\n"
                                           "x = 42\n"
                                           "x, y = f(x)\n"
                                           "x, y = (y, x)\n", env_in)

        self.assertEqual(len(env_out), len(env_in) + 3)
        self.assertErrors(1, err)
        self.assertEqual(9, len(dec))

    def test_block(self):
        """
        Tests the validation of statement blocks.
        """

        env_in = static.SpektakelValidator.environment_default()

        node, env_out, dec, err = validate("var x, y, z\n"
                                           "x, y, z = 42, 42, 42\n"
                                           "var y = 4711 + y\n", env_in)

        self.assertEqual(len(env_out), len(env_in) + 3)
        self.assertErrors(0, err)
        self.assertEqual(8, len(dec))

        referents_y = [v for k, v in dec.items() if isinstance(k, syntax.Identifier) and k.name == "y"]

        self.assertEqual(2, len(referents_y))
        self.assertEqual(1, len(set(referents_y)))

    def test_return(self):
        """
        Tests the validation of return statements.
        """

        env_in = static.SpektakelValidator.environment_default()

        node, env_out, dec, err = validate("return 42\n"
                                           "def f(x):\n"
                                           "    return x\n"
                                           "def g(x):\n"
                                           "    return\n", env_in)

        self.assertEqual(len(env_out), len(env_in) + 2)
        self.assertErrors(1, err)  # return outside procedure.
        self.assertEqual(4, len(dec))

    def test_raise(self):
        """
        Tests the validation of raise statements.
        """

        env_in = static.SpektakelValidator.environment_default()

        node, env_out, dec, err = validate("raise # Should work.\n"
                                           "def f(x):\n"
                                           "    return x\n"
                                           "raise f() # This *should* work outside a catch block!\n"
                                           "try:\n"
                                           "    pass\n"
                                           "except:\n"
                                           "    raise # Should just work.\n", env_in)

        self.assertEqual(len(env_out), len(env_in) + 1)
        self.assertErrors(0, err)
        self.assertEqual(3, len(dec))

    def test_loop_jumps(self):
        """
        Tests the validation of 'break' and 'continue'.
        """

        env_in = static.SpektakelValidator.environment_default()

        node, env_out, dec, err = validate("break # Must fail, because no loop.\n"
                                           "continue # Must fail, because no loop.\n"
                                           "while True:\n"
                                           "    break\n"
                                           "while False:\n"
                                           "    continue\n"
                                           "for x in items:\n"
                                           "    break\n"
                                           "for y in items:\n"
                                           "    continue", env_in)

        self.assertEqual(len(env_in), len(env_out))
        self.assertErrors(4, err)
        self.assertEqual(6, len(dec))

    def test_if(self):
        """
        Tests the validation of 'if' statements.
        """

        env_in = static.SpektakelValidator.environment_default()

        node, env_out, dec, err = validate("if meaning_of_life == 42:\n"
                                           "    print(\"easy peasy\")\n"
                                           "elif flyable(pig):\n"
                                           "    print(\"We're lucky!\")\n"
                                           "else:\n"
                                           "    print(\"No free lunch :-(\")\n"
                                           "\n"
                                           "if iq > temp_room():\n"
                                           "    print(\"You're a genius!\")\n"
                                           "else:\n"
                                           "    print(\"Do you want ice cream?\")\n"
                                           "if done:\n"
                                           "    print(\"No more work to do :-)\")", env_in)

        self.assertEqual(len(env_in), len(env_out))
        self.assertErrors(12, err)
        self.assertEqual(7, len(dec))

    def test_while(self):
        """
        Tests the validation of 'while' loops.
        """

        env_in = static.SpektakelValidator.environment_default()

        node, env_out, dec, err = validate("while True:\n"
                                           "    pass\n"
                                           "while False:\n"
                                           "    do_some_work()", env_in)

        self.assertEqual(len(env_in), len(env_out))
        self.assertErrors(1, err)
        self.assertEqual(2, len(dec))

    def test_for(self):
        """
        Tests the validation of 'for' loops.
        """

        env_in = static.SpektakelValidator.environment_default()

        node, env_out, dec, err = validate("var items\n"
                                           "for x in items:\n"
                                           "    work(x)\n"
                                           "for (a, (b, c)) in items:\n"
                                           "    work(b)\n"
                                           "for 42 in items:\n"
                                           "    learn(0 == 1)\n", env_in)

        self.assertEqual(len(env_in) + 1, len(env_out))
        self.assertErrors(4, err)
        self.assertEqual(7, len(dec))

    def test_try(self):
        """
        Tests the validation of 'try' statements.
        """

        env_in = static.SpektakelValidator.environment_default()

        node, env_out, dec, err = validate("try:\n"
                                           "    work()\n"
                                           "except:\n"
                                           "    print(\"An error, sadly\")\n"
                                           "\n"
                                           "try:\n"
                                           "    work()\n"
                                           "finally:\n"
                                           "    print(\"It's over\")\n"
                                           "\n"
                                           "try:\n"
                                           "    raise Exception()\n"
                                           "except Exception:\n"
                                           "    raise\n"
                                           "try:\n"
                                           "    raise Exception()\n"
                                           "except Exception:\n"
                                           "    raise\n"
                                           "finally:\n"
                                           "    print(\"Done.\")\n"
                                           "\n"
                                           "try:\n"
                                           "   raise Exception()\n"
                                           "except Exception as e:\n"
                                           "   print(e)\n"
                                           "except Fception:\n"
                                           "   print(\"Weird\")\n"
                                           "except:\n"
                                           "   print(\"No idea\")", env_in)

        self.assertEqual(len(env_in), len(env_out))
        self.assertErrors(15, err)
        self.assertEqual(6, len(dec))

    def test_var(self):
        """
        Tests the validation of variable declarations.
        """

        env_in = static.SpektakelValidator.environment_default()

        node, env_out, dec, err = validate("var x\n"
                                           "var x\n"
                                           "var 42\n"
                                           "var y = x > 0\n"
                                           "var (a, (b, c)) = f(y)\n"
                                           "var a, b, c, d = g(y)\n"
                                           "var z = z", env_in)

        self.assertEqual(len(env_in) + 7, len(env_out))
        self.assertErrors(4, err)
        self.assertEqual(4, len(dec))

    def test_prop(self):
        """
        Tests the validation of property declarations.
        """

        env_in = static.SpektakelValidator.environment_default()

        node, env_out, dec, err = validate("prop fail: # Must fail, because it's outside a class.\n"
                                           "  get:\n"
                                           "    return 42\n"
                                           "class C:\n"
                                           "\n"
                                           "  var x = 42\n"
                                           "\n"
                                           "  prop simple:\n"
                                           "    get:\n"
                                           "      return 42\n"
                                           "  prop writable:\n"
                                           "    get:\n"
                                           "      return self.x\n"
                                           "    set value:\n"
                                           "      self.x = value\n"
                                           "  prop simple: # Over-declaring should not be possible.\n"
                                           "    get:\n"
                                           "      return 42", env_in)

        self.assertEqual(len(env_in) + 2, len(env_out))
        self.assertErrors(2, err)
        self.assertEqual(12, len(dec))

    def test_proc(self):
        """
        Tests the validation of procedure declarations.
        """

        env_in = static.SpektakelValidator.environment_default()

        node, env_out, dec, err = validate("def dummy():\n"
                                           "  return 42\n"
                                           "def id(x):\n"
                                           "  return x\n"
                                           "def sum(x, y, z):\n"
                                           "  return x + y + z\n"
                                           "def test(a):\n"
                                           "  def t(b):\n"
                                           "    return a + b\n"
                                           "  return t\n"
                                           "def fib(i):\n"
                                           "    if i <= 1:\n"
                                           "      return i\n"
                                           "    else:\n"
                                           "      return fib(i - 2) + fib(i - 1)\n"
                                           "def test (x, x): # Should fail, because it's nonsense.\n"
                                           "  return x\n"
                                           "def even(x):\n"
                                           "  if x == 0:\n"
                                           "    return True\n"
                                           "  else:\n"
                                           "    return odd (x - 1) # Fails, because 'odd' is undefined.\n"
                                           "var odd\n"
                                           "def even(x):\n"
                                           "  if x == 0:\n"
                                           "    return True\n"
                                           "  else:\n"
                                           "    return odd (x - 1)\n"
                                           "\n"
                                           "def odd(x):\n"
                                           "  if x == 0:\n"
                                           "    return False\n"
                                           "  else:\n"
                                           "    return even(x - 1)\n"
                                           "", env_in)

        self.assertEqual(len(env_in) + 7, len(env_out))
        self.assertErrors(2, err)
        self.assertEqual(49, len(dec))

    def test_class(self):
        """
        Tests the validation of class declarations.
        """

        env_in = static.SpektakelValidator.environment_default()

        node, env_out, dec, err = validate("class C():\n"
                                           "  pass\n"
                                           "class D(C):\n"
                                           "  pass\n"
                                           "class Point:\n"
                                           "  var _x, _y\n"
                                           "  def __init__(x, y):\n"
                                           "    self._x, self._y = x, y\n"
                                           "  prop x:\n"
                                           "    get:\n"
                                           "        return self._x\n"
                                           "  prop y:\n"
                                           "    get:\n"
                                           "        return self._y\n"
                                           "\n"
                                           "def p():\n"
                                           "  class A(): # Error: Class definitions are not allowed in procedures.\n"
                                           "    pass\n"
                                           "\n"
                                           "class A(C, D):\n"
                                           "  pass\n"
                                           "class Z(Y): # Y undefined.\n"
                                           "  pass\n"
                                           "\n"
                                           "class F():\n"
                                           "  def f():\n"
                                           "    return 42\n"
                                           "  prop f: # Error: Duplicte member name.\n"
                                           "    get:\n"
                                           "      return 42\n"
                                           "\n"
                                           "class E:\n"
                                           "  \"\"\"\n"
                                           "  A fun little test class.\n"
                                           "  \"\"\"\n"
                                           "  def p():\n"
                                           "    \"\"\"\n"
                                           "    This works :-)\n"
                                           "    \"\"\"\n"
                                           "    return 1377\n"
                                           "  prop q:\n"
                                           "    \"\"\"\n"
                                           "    This is a property.\n"
                                           "    \"\"\"\n"
                                           "    get:\n"
                                           "        return 4711\n"
                                           "  p() # Error.\n"
                                           "\n"
                                           "13 # This is allowed.\n"
                                           "", env_in)

        self.assertEqual(len(env_in) + 8, len(env_out))
        self.assertErrors(4, err)
        self.assertEqual(30, len(dec))

    def test_import(self):
        """
        Tests the validation of import statements.
        """
        root = os.path.join(os.path.dirname(os.path.realpath(__file__)), "samples_import")

        finder = modules.build_default_finder([os.path.join(root, "library")])
        validator = static.SpektakelValidator(finder)

        for fn in os.listdir(root):
            name, ext = os.path.splitext(fn)
            if ext != ".spek":
                continue

            name, *sums = name.split("_")
            envsize, numerrors, decsize = map(int, sums)

            with self.subTest(example=name):
                with open(os.path.join(root, fn), 'r') as sample:
                    lexer = syntax.SpektakelLexer(sample)
                    ast = syntax.SpektakelParser.parse_block(lexer)
                    env_in = static.SpektakelValidator.environment_default()
                    env_out, dec, err = validator.validate(ast, env_in)

                    self.assertEqual(len(env_in) + envsize, len(env_out))
                    self.assertErrors(numerrors, err)
                    self.assertEqual(decsize, len(dec))

    def test_examples(self):
        """
        Tests the validator on all spek examples.
        """

        roots = ["examples", "library"]
        roots = [os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", r) for r in roots]

        finder = modules.build_default_finder(roots)
        validator = static.SpektakelValidator(finder)

        for path in example_paths:
            _, filename = os.path.split(path)
            with self.subTest(example=os.path.splitext(filename)[0]):
                modules.SpekFileModuleSpecification(path, validator).resolve()
