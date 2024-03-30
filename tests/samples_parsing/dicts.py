from lang.spek import ast

samples = {
"""
var x = {}
""": ast.VariableDeclaration,
"""
var x = {1: 2}
""": ast.VariableDeclaration,
"""
var x = {1: 2, 3: 4}
""": ast.VariableDeclaration,
}