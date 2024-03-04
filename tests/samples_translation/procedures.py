from engine.functional.values import VAttributeError
from engine.tasks.interaction import num_interactions_possible

samples = {


"""
from interaction import never

def foo():
    return 42
    
var x = foo()

await never()
""": ((2, 1, num_interactions_possible), {"x": 42}),

"""
from interaction import never

def foo(x):
    return x + 1

var x = foo(42)

await never()
""": ((2, 1, num_interactions_possible), {"x": 43}),


"""
from interaction import never

def foo(x):
    return x + 1
    
def bar(x):
    return x - 1

var x = bar(bar(foo(42) - bar(42)))

await never()
""": ((2, 1, num_interactions_possible), {"x": 0}),

"""
from interaction import never

var x = 42

def foo():
    x = x + 1    
    
foo()
foo()

await never()
""": ((2, 1, num_interactions_possible), {"x": 44}),


"""
from interaction import never

var x = 0

def small(x):
    return x < 42
    
def even(x):
    return x % 2 == 0
    
def increment():
    x = x + 1 

if small(x) and even(x):
    increment()

await never()
""": ((2, 1, num_interactions_possible), {"x": 1}),

"""
from interaction import never

var x = 0

def small(x):
    return x < 42  

def even(x):
    return x % 2 == 0

def increment():
    x = x + 1 

while small(x) or even(x):
    increment()

await never()
""": ((2, 1, num_interactions_possible), {"x": 43}),

"""
from interaction import never

def even(x):
    return x % 2 == 0

def foo(x):
    if even(x):
        return True
    return False
    
var x = foo(42) and not foo(43)

await never()
""": ((2, 1, num_interactions_possible), {"x": True}),

"""
from interaction import never

def geq(x, y):        
    while x >= 0:        
        if x == y:
            return True
        x = x - 1
    return False

var x = geq(17, 12) and not geq(5, 7)

await never()
""": ((2, 1, num_interactions_possible), {"x": True}),

"""
from interaction import never

def geq(x, y):    

    if x == 0:
        return y == 0
    if x == y:
        return True
    
    return geq(x - 1, y)

var x = geq(17, 12) and not geq(5, 7)

await never()
""": ((2, 1, num_interactions_possible), {"x": True}),

"""
from interaction import never

var odd
def even(x):
     if x == 0:
        return True
     return odd(x - 1)
    
def _odd(x):
    if x == 0:
        return False
    return even(x - 1)
odd = _odd

var x = even(4) and not even(5)

await never()
""": ((2, 1, num_interactions_possible), {"x": True}),

"""
from interaction import never

def foo(x):
    return x + 1
    
var a = foo(42)

def bar(x):
    if x <= 0:
        return x
    else:
        return foo(x - 1)
    
foo = bar

var b = foo(42)

await never()
""": ((2, 1, num_interactions_possible), {"a": 43, "b": 0}),

"""
from interaction import never

def foo():
    return AttributeError("Test")

var x = foo()

await never()
""": ((2, 1, num_interactions_possible), {"x": VAttributeError("Test")}),

}