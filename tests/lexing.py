import unittest
from io import StringIO
from syntax.lexer import Lexer, PythonesqueLexicalGrammar

kw_python = ["False", "await", "else", "import", "pass", "None", "break", "except", "in", "raise", "True", "class",
             "finally", "is", "return", "and", "continue", "for", "lambda", "try", "as", "def", "from", "nonlocal",
             "while", "assert", "del", "global", "not", "with", "async", "elif", "if", "or", "yield"]
sep_python = ["+", "-", "*", "**", "/", "//", "%", "@", "<<", ">>", "&", "|", "^", "~", ":=", "<", ">", "<=", ">=",
              "==", "!=", "(", ")", "[", "]", "{", "}", ",", ":", ".", ";", "@", "=", "->", "+=", "-=", "*=", "/=",
              "//=", "%=", "@=", "&=", "|=", "^=", ">>=", "<<=", "**="]

sample_python1 = """
def perm(l):
        # Compute the list of all permutations of l
    if len(l) <= 1:
                  return [l]
    r = []
    for i in range(len(l)):
             s = l[:i] + l[i+1:]
             p = perm(s)
             for x in p:
              r.append(l[i:i+1] + x)
    return r
"""


class TestLexer(unittest.TestCase):

    def test_construction(self):
        """
        Tests if the usual workflow of building a lexer works without crashes.
        :return:
        """
        g_python = PythonesqueLexicalGrammar(kw_python, sep_python)
        code = StringIO(sample_python1)
        Lexer(g_python, code)

    def test_helloworld(self):
        s = 'hello world'
        self.assertEqual(s.split(), ['hello', 'world'])
        # check that s.split fails when the separator is not a string
        with self.assertRaises(TypeError):
            s.split(2)