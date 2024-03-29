from lang.pythonesque import TokenType

sample01 = """
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
tokens01 = [(TokenType.KEYWORD, "def"),
            (TokenType.IDENTIFIER, "perm"),
            (TokenType.KEYWORD, "("),
            (TokenType.IDENTIFIER, "l"),
            (TokenType.KEYWORD, ")"),
            (TokenType.KEYWORD, ":"),
            (TokenType.NEWLINE, "\n"),
            (TokenType.INDENT, None),
            (TokenType.KEYWORD, "if"),
            (TokenType.IDENTIFIER, "len"),
            (TokenType.KEYWORD, "("),
            (TokenType.IDENTIFIER, "l"),
            (TokenType.KEYWORD, ")"),
            (TokenType.KEYWORD, "<="),
            (TokenType.LITERAL, "1"),
            (TokenType.KEYWORD, ":"),
            (TokenType.NEWLINE, "\n"),
            (TokenType.INDENT, None),
            (TokenType.KEYWORD, "return"),
            (TokenType.KEYWORD, "["),
            (TokenType.IDENTIFIER, "l"),
            (TokenType.KEYWORD, "]"),
            (TokenType.NEWLINE, "\n"),
            (TokenType.DEDENT, None),
            (TokenType.IDENTIFIER, "r"),
            (TokenType.KEYWORD, "="),
            (TokenType.KEYWORD, "["),
            (TokenType.KEYWORD, "]"),
            (TokenType.NEWLINE, "\n"),
            (TokenType.KEYWORD, "for"),
            (TokenType.IDENTIFIER, "i"),
            (TokenType.KEYWORD, "in"),
            (TokenType.IDENTIFIER, "range"),
            (TokenType.KEYWORD, "("),
            (TokenType.IDENTIFIER, "len"),
            (TokenType.KEYWORD, "("),
            (TokenType.IDENTIFIER, "l"),
            (TokenType.KEYWORD, ")"),
            (TokenType.KEYWORD, ")"),
            (TokenType.KEYWORD, ":"),
            (TokenType.NEWLINE, "\n"),
            (TokenType.INDENT, None),
            (TokenType.IDENTIFIER, "s"),
            (TokenType.KEYWORD, "="),
            (TokenType.IDENTIFIER, "l"),
            (TokenType.KEYWORD, "["),
            (TokenType.KEYWORD, ":"),
            (TokenType.IDENTIFIER, "i"),
            (TokenType.KEYWORD, "]"),
            (TokenType.KEYWORD, "+"),
            (TokenType.IDENTIFIER, "l"),
            (TokenType.KEYWORD, "["),
            (TokenType.IDENTIFIER, "i"),
            (TokenType.KEYWORD, "+"),
            (TokenType.LITERAL, "1"),
            (TokenType.KEYWORD, ":"),
            (TokenType.KEYWORD, "]"),
            (TokenType.NEWLINE, "\n"),
            (TokenType.IDENTIFIER, "p"),
            (TokenType.KEYWORD, "="),
            (TokenType.IDENTIFIER, "perm"),
            (TokenType.KEYWORD, "("),
            (TokenType.IDENTIFIER, "s"),
            (TokenType.KEYWORD, ")"),
            (TokenType.NEWLINE, "\n"),
            (TokenType.KEYWORD, "for"),
            (TokenType.IDENTIFIER, "x"),
            (TokenType.KEYWORD, "in"),
            (TokenType.IDENTIFIER, "p"),
            (TokenType.KEYWORD, ":"),
            (TokenType.NEWLINE, "\n"),
            (TokenType.INDENT, None),
            (TokenType.IDENTIFIER, "r"),
            (TokenType.KEYWORD, "."),
            (TokenType.IDENTIFIER, "append"),
            (TokenType.KEYWORD, "("),
            (TokenType.IDENTIFIER, "l"),
            (TokenType.KEYWORD, "["),
            (TokenType.IDENTIFIER, "i"),
            (TokenType.KEYWORD, ":"),
            (TokenType.IDENTIFIER, "i"),
            (TokenType.KEYWORD, "+"),
            (TokenType.LITERAL, "1"),
            (TokenType.KEYWORD, "]"),
            (TokenType.KEYWORD, "+"),
            (TokenType.IDENTIFIER, "x"),
            (TokenType.KEYWORD, ")"),
            (TokenType.NEWLINE, "\n"),
            (TokenType.DEDENT, None),
            (TokenType.DEDENT, None),
            (TokenType.KEYWORD, "return"),
            (TokenType.IDENTIFIER, "r"),
            (TokenType.NEWLINE, "\n"),
            (TokenType.DEDENT, None)
            ]


sample02 = """
if 1900 < year < 2100 and 1 <= month <= 12 \
   and 1 <= day <= 31 and 0 <= hour < 24 \
   and 0 <= minute < 60 and 0 <= second < 60:   # Looks like a valid date
        return 1
"""


tokens02 = [(TokenType.KEYWORD, "if"),
            (TokenType.LITERAL, "1900"),
            (TokenType.KEYWORD, "<"),
            (TokenType.IDENTIFIER, "year"),
            (TokenType.KEYWORD, "<"),
            (TokenType.LITERAL, "2100"),
            (TokenType.KEYWORD, "and"),

            (TokenType.LITERAL, "1"),
            (TokenType.KEYWORD, "<="),
            (TokenType.IDENTIFIER, "month"),
            (TokenType.KEYWORD, "<="),
            (TokenType.LITERAL, "12"),

            (TokenType.KEYWORD, "and"),

            (TokenType.LITERAL, "1"),
            (TokenType.KEYWORD, "<="),
            (TokenType.IDENTIFIER, "day"),
            (TokenType.KEYWORD, "<="),
            (TokenType.LITERAL, "31"),

            (TokenType.KEYWORD, "and"),

            (TokenType.LITERAL, "0"),
            (TokenType.KEYWORD, "<="),
            (TokenType.IDENTIFIER, "hour"),
            (TokenType.KEYWORD, "<"),
            (TokenType.LITERAL, "24"),

            (TokenType.KEYWORD, "and"),

            (TokenType.LITERAL, "0"),
            (TokenType.KEYWORD, "<="),
            (TokenType.IDENTIFIER, "minute"),
            (TokenType.KEYWORD, "<"),
            (TokenType.LITERAL, "60"),

            (TokenType.KEYWORD, "and"),

            (TokenType.LITERAL, "0"),
            (TokenType.KEYWORD, "<="),
            (TokenType.IDENTIFIER, "second"),
            (TokenType.KEYWORD, "<"),
            (TokenType.LITERAL, "60"),

            (TokenType.KEYWORD, ":"),
            (TokenType.NEWLINE, "\n"),
            (TokenType.INDENT, None),
            (TokenType.KEYWORD, "return"),
            (TokenType.LITERAL, "1"),
            (TokenType.NEWLINE, "\n"),
            (TokenType.DEDENT, None),
            ]


sample03 = """
month_names = [\"Januari\", \"Februari\", \"Maart\",      # These are the
               \"April\",   \"Mei\",      \"Juni\",       # Dutch names
               \"Juli\",    \"Augustus\", \"September\",  # for the months
               \"Oktober\", \"November\", \"December\"]   # of the year
"""


tokens03 = [(TokenType.IDENTIFIER, "month_names"),
            (TokenType.KEYWORD, "="),
            (TokenType.KEYWORD, "["),
            (TokenType.LITERAL, "\"Januari\""),
            (TokenType.KEYWORD, ","),
            (TokenType.LITERAL, "\"Februari\""),
            (TokenType.KEYWORD, ","),
            (TokenType.LITERAL, "\"Maart\""),
            (TokenType.KEYWORD, ","),
            (TokenType.LITERAL, "\"April\""),
            (TokenType.KEYWORD, ","),
            (TokenType.LITERAL, "\"Mei\""),
            (TokenType.KEYWORD, ","),
            (TokenType.LITERAL, "\"Juni\""),
            (TokenType.KEYWORD, ","),
            (TokenType.LITERAL, "\"Juli\""),
            (TokenType.KEYWORD, ","),
            (TokenType.LITERAL, "\"Augustus\""),
            (TokenType.KEYWORD, ","),
            (TokenType.LITERAL, "\"September\""),
            (TokenType.KEYWORD, ","),
            (TokenType.LITERAL, "\"Oktober\""),
            (TokenType.KEYWORD, ","),
            (TokenType.LITERAL, "\"November\""),
            (TokenType.KEYWORD, ","),
            (TokenType.LITERAL, "\"December\""),
            (TokenType.KEYWORD, "]"),
            (TokenType.NEWLINE, "\n"),
            ]


sample04 = "e = m * c ** 2"
tokens04 = [(TokenType.IDENTIFIER, "e"),
            (TokenType.KEYWORD, "="),
            (TokenType.IDENTIFIER, "m"),
            (TokenType.KEYWORD, "*"),
            (TokenType.IDENTIFIER, "c"),
            (TokenType.KEYWORD, "**"),
            (TokenType.LITERAL, "2"),
            (TokenType.NEWLINE, "\n"),
            ]

sample05 = "   3.1415926"
tokens05 = [(TokenType.INDENT, None),
            (TokenType.LITERAL, "3.1415926"),
            (TokenType.NEWLINE, "\n"),
            (TokenType.DEDENT, None)
            ]


sample06 = """\" Hello, this is a rather lengthy string.\"
\"This is an even much much longer string! It is in fact so long, that not even a chunk size of 1024 should suffice to hold it in one chunk. Lorem ipsum dolor sit amet, consectetur adipisici elit, sed eiusmod tempor incidunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquid ex ea commodi consequat. Quis aute iure reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint obcaecat cupiditat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum. Lorem ipsum dolor sit amet, consectetur adipisici elit, sed eiusmod tempor incidunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquid ex ea commodi consequat. Quis aute iure reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint obcaecat cupiditat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum. Lorem ipsum dolor sit amet, consectetur adipisici elit, sed eiusmod tempor incidunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquid ex ea commodi consequat. Quis aute iure reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint obcaecat cupiditat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.\"
\"\"\"
Let's try the same with a nice multi-line string:
Lorem ipsum dolor sit amet, consectetur adipisici elit, sed eiusmod tempor incidunt ut labore et dolore magna aliqua.
Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquid ex ea commodi consequat.
Quis aute iure reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.
Excepteur sint obcaecat cupiditat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.
Lorem ipsum dolor sit amet, consectetur adipisici elit, sed eiusmod tempor incidunt ut labore et dolore magna aliqua.
Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquid ex ea commodi consequat.
Quis aute iure reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.
Excepteur sint obcaecat cupiditat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.
Lorem ipsum dolor sit amet, consectetur adipisici elit, sed eiusmod tempor incidunt ut labore et dolore magna aliqua.
Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquid ex ea commodi consequat.
Quis aute iure reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.
Excepteur sint obcaecat cupiditat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.
Lorem ipsum dolor sit amet, consectetur adipisici elit, sed eiusmod tempor incidunt ut labore et dolore magna aliqua.
Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquid ex ea commodi consequat.
Quis aute iure reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.
Excepteur sint obcaecat cupiditat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.
\"\"\"
now_let_us_have_some_really_long_identifier_to_make_sure_that_the_lexer_can_handle_it
3.14159265359654634769089756345678909876543456789098765432345
314159265359654634769089756345678909876543456789098765432345
whil"""
tokens06 = [(TokenType.LITERAL, "\" Hello, this is a rather lengthy string.\""),
            (TokenType.NEWLINE, "\n"),
            (TokenType.LITERAL, "\"This is an even much much longer string! It is in fact so long, that not even a chunk size of 1024 should suffice to hold it in one chunk. Lorem ipsum dolor sit amet, consectetur adipisici elit, sed eiusmod tempor incidunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquid ex ea commodi consequat. Quis aute iure reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint obcaecat cupiditat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum. Lorem ipsum dolor sit amet, consectetur adipisici elit, sed eiusmod tempor incidunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquid ex ea commodi consequat. Quis aute iure reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint obcaecat cupiditat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum. Lorem ipsum dolor sit amet, consectetur adipisici elit, sed eiusmod tempor incidunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquid ex ea commodi consequat. Quis aute iure reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint obcaecat cupiditat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.\""),
            (TokenType.NEWLINE, "\n"),
            (TokenType.LITERAL, """\"\"\"
Let's try the same with a nice multi-line string:
Lorem ipsum dolor sit amet, consectetur adipisici elit, sed eiusmod tempor incidunt ut labore et dolore magna aliqua.
Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquid ex ea commodi consequat.
Quis aute iure reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.
Excepteur sint obcaecat cupiditat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.
Lorem ipsum dolor sit amet, consectetur adipisici elit, sed eiusmod tempor incidunt ut labore et dolore magna aliqua.
Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquid ex ea commodi consequat.
Quis aute iure reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.
Excepteur sint obcaecat cupiditat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.
Lorem ipsum dolor sit amet, consectetur adipisici elit, sed eiusmod tempor incidunt ut labore et dolore magna aliqua.
Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquid ex ea commodi consequat.
Quis aute iure reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.
Excepteur sint obcaecat cupiditat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.
Lorem ipsum dolor sit amet, consectetur adipisici elit, sed eiusmod tempor incidunt ut labore et dolore magna aliqua.
Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquid ex ea commodi consequat.
Quis aute iure reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.
Excepteur sint obcaecat cupiditat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.
\"\"\""""),
            (TokenType.NEWLINE, "\n"),
            (TokenType.IDENTIFIER, "now_let_us_have_some_really_long_identifier_to_make_sure_that_the_lexer_can_handle_it"),
            (TokenType.NEWLINE, "\n"),
            (TokenType.LITERAL, "3.14159265359654634769089756345678909876543456789098765432345"),
            (TokenType.NEWLINE, "\n"),
            (TokenType.LITERAL, "314159265359654634769089756345678909876543456789098765432345"),
            (TokenType.NEWLINE, "\n"),
            (TokenType.IDENTIFIER, "whil"),
            (TokenType.NEWLINE, "\n"),
            ]

sample07 = """
if a ** 2 + b ** 2 == c ** 2:
    return True
else:
    panic()
"""
tokens07 =  [(TokenType.KEYWORD, "if"),
            (TokenType.IDENTIFIER, "a"),
            (TokenType.KEYWORD, "**"),
            (TokenType.LITERAL, "2"),
            (TokenType.KEYWORD, "+"),
            (TokenType.IDENTIFIER, "b"),
            (TokenType.KEYWORD, "**"),
            (TokenType.LITERAL, "2"),
            (TokenType.KEYWORD, "=="),
            (TokenType.IDENTIFIER, "c"),
            (TokenType.KEYWORD, "**"),
            (TokenType.LITERAL, "2"),
            (TokenType.KEYWORD, ":"),
            (TokenType.NEWLINE, "\n"),
            (TokenType.INDENT, None),
             (TokenType.KEYWORD, "return"),
             (TokenType.KEYWORD, "True"),
             (TokenType.NEWLINE, "\n"),
             (TokenType.DEDENT, None),
             (TokenType.KEYWORD, "else"),
             (TokenType.KEYWORD, ":"),
             (TokenType.NEWLINE, "\n"),
             (TokenType.INDENT, None),
             (TokenType.IDENTIFIER, "panic"),
             (TokenType.KEYWORD, "("),
             (TokenType.KEYWORD, ")"),
             (TokenType.NEWLINE, "\n"),
             (TokenType.DEDENT, None),
             ]

sample08 = """
class C(B):

    def __init__(self, x, y):
        self._x = x
        self._y = y

    def x():
        return self._x

"""
tokens08 =  [(TokenType.KEYWORD, "class"),
             (TokenType.IDENTIFIER, "C"),
             (TokenType.KEYWORD, "("),
             (TokenType.IDENTIFIER, "B"),
             (TokenType.KEYWORD, ")"),
             (TokenType.KEYWORD, ":"),
             (TokenType.NEWLINE, "\n"),
             (TokenType.INDENT, None),
             (TokenType.KEYWORD, "def"),
             (TokenType.IDENTIFIER, "__init__"),
             (TokenType.KEYWORD, "("),
             (TokenType.IDENTIFIER, "self"),
             (TokenType.KEYWORD, ","),
             (TokenType.IDENTIFIER, "x"),
             (TokenType.KEYWORD, ","),
             (TokenType.IDENTIFIER, "y"),
             (TokenType.KEYWORD, ")"),
             (TokenType.KEYWORD, ":"),
             (TokenType.NEWLINE, "\n"),
             (TokenType.INDENT, None),
             (TokenType.IDENTIFIER, "self"),
             (TokenType.KEYWORD, "."),
             (TokenType.IDENTIFIER, "_x"),
             (TokenType.KEYWORD, "="),
             (TokenType.IDENTIFIER, "x"),
             (TokenType.NEWLINE, "\n"),
             (TokenType.IDENTIFIER, "self"),
             (TokenType.KEYWORD, "."),
             (TokenType.IDENTIFIER, "_y"),
             (TokenType.KEYWORD, "="),
             (TokenType.IDENTIFIER, "y"),
             (TokenType.NEWLINE, "\n"),
             (TokenType.DEDENT, None),
             (TokenType.KEYWORD, "def"),
             (TokenType.IDENTIFIER, "x"),
             (TokenType.KEYWORD, "("),
             (TokenType.KEYWORD, ")"),
             (TokenType.KEYWORD, ":"),
             (TokenType.NEWLINE, "\n"),
             (TokenType.INDENT, None),
             (TokenType.KEYWORD, "return"),
             (TokenType.IDENTIFIER, "self"),
             (TokenType.KEYWORD, "."),
             (TokenType.IDENTIFIER, "_x"),
             (TokenType.NEWLINE, "\n"),
             (TokenType.DEDENT, None),
             (TokenType.DEDENT, None)
             ]


sample09 = "\"\"\"This is a \"Hello World\" test.\"\"\""
tokens09 = [(TokenType.LITERAL, "\"\"\"This is a \"Hello World\" test.\"\"\""),
            (TokenType.NEWLINE, "\n")]


vars = list(locals().items())
samples = {}
for vname, v in vars:
    if vname.startswith("sample"):
        idx = int(vname[len("sample"):])
        p = (v, eval("tokens{:02d}".format(idx)))
        samples[vname] = p
