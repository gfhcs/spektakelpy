from lang.spek import ast

samples = {
"""
var (x,) = (1,)
""": ast.VariableDeclaration,
"""
var x,
x, = 1,
""": ast.VariableDeclaration,
"""
var x, = 1,
""": ast.VariableDeclaration,
"""
var x, y = 1, 2
""": ast.VariableDeclaration,
"""
def foo():
    return 42, 4711
""": ast.ProcedureDefinition,
"""
def foo():
    return 42,
""": ast.ProcedureDefinition

}