from lang.spek import ast

samples = {
"""
prop location:
    get(self):
        return self.x
    set(self, value):
        self.x = value
""": ast.PropertyDefinition,
"""
prop colour:
    get(self):
        return self.colour
""": ast.PropertyDefinition
}