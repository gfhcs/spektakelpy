from lang.spek import ast

samples = {
"""
class C:
    pass
""": ast.ClassDefinition,
"""
class A(B):
    pass
""": ast.ClassDefinition,
"""
class C(B):
    
    def __init__(self, x, y):
        self._x = x
        self._y = y
        
    prop x:
        get(self):
            return self._x
    
    prop y:
        get(self):
            return self._y
""": ast.ClassDefinition,

}