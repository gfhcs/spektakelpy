from lang.spek import ast

samples = {
"""
def foo():
    return 42
""": ast.ProcedureDefinition,
"""
def abs(x):
    if x >= 0:
        return x
    else:
        return -x
""": ast.ProcedureDefinition,
"""
def max(x, y):
    if x >= y:
        return x
    else:
        return y
""": ast.ProcedureDefinition,
"""
def max3(x, y, z):
    return max(x, max(y, z))
""": ast.ProcedureDefinition

}