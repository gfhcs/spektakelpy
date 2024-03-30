from lang.spek import ast

samples = {
"""
var [x] = (1,)
""": ast.VariableDeclaration,
"""
var [x, ] = (1,)
""": ast.VariableDeclaration,
"""
var [x, y] = (1, 2)
""": ast.VariableDeclaration,
"""
var [x, ]
""": ast.VariableDeclaration,
"""
var [x]
""": ast.VariableDeclaration,
"""
var x = []
""": ast.VariableDeclaration,
"""
var x = [1, 2, 3]
""": ast.VariableDeclaration,
}