from syntax.phrasal import ast

samples = {
"""
prop location:
    get:
        return self.x
    set value:
        self.x = value
""": ast.PropertyDefinition,
"""
prop colour:
    get:
        return self.colour
""": ast.PropertyDefinition
}