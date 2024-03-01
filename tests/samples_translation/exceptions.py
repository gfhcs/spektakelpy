from engine.functional.values import VException, VTypeError
from engine.tasks.interaction import num_interactions_possible

samples = {

"""
from interaction import never
var x = Exception("Hello world!")
await never()
""": ((2, 1, num_interactions_possible), {"x": VException("Hello world!")}),

"""
from interaction import never
var x = TypeError("Hello world!")
await never()
""": ((2, 1, num_interactions_possible), {"x": VTypeError("Hello world!")}),

"""
from interaction import never
var x = isinstance(TypeError("Hello world!"), Exception)
await never()
""": ((2, 1, num_interactions_possible), {"x": True}),

"""
from interaction import never
raise Exception("This brings the task down!")
await never()
""": ((2, 1, num_interactions_possible), {}),

"""
from interaction import never

var x
try:
    raise Exception("This brings the task down!")
    x = False
except:
    x = True
    
await never()
""": ((2, 1, num_interactions_possible), {"x": True}),

"""
from interaction import never

var x
try:
    raise Exception("This brings the task down!")
except TypeError:
    x = False
except:
    x = True

await never()
""": ((2, 1, num_interactions_possible), {"x": True}),

"""
from interaction import never

var x = False
try:
    raise Exception("This brings the task down!")
except Exception as ex:
    x = isinstance(ex, Exception)

await never()
""": ((2, 1, num_interactions_possible), {"x": True}),

"""
from interaction import never

var x = False
try:
    x = False
except:
    x = False
finally:
    x = True

await never()
""": ((2, 1, num_interactions_possible), {"x": True}),


"""
from interaction import never

var x = False
try:
    raise Exception("This brings the task down!")
    x = False
except:
    x = False
finally:
    x = True

await never()
""": ((2, 1, num_interactions_possible), {"x": True}),

"""
from interaction import never

var x = False
try:
    if False:
            x = False
    else:
        raise Exception("This brings the task down!")
    x = False
except:
    x = True

await never()
""": ((2, 1, num_interactions_possible), {"x": True}),


"""
from interaction import never

var i = 0
var x = False
try:
    while True:
        i = i + x
        if i > 10:
            raise Exception("To big!")
except:
    x = True

await never()
""": ((2, 1, num_interactions_possible), {"x": True, "i": 11}),


"""
from interaction import never

var x, y, z = False, False, False

def bar(i):
    try:
        return i % 2 == 0
    except AttributeError:
        return
    finally:
        y = True

def foo(i):
    try:
        bar(i)
    except TypeError:
        x = True
        raise
    
try:
    foo("hello")
except:
    z = True

await never()
""": ((2, 1, num_interactions_possible), {"x": True, "y": True, "z": True}),

"""
from interaction import never

var x, y = False, False

try:
    try:
        raise Exception("A")
        x = False
    except:
        raise TypeError("B")
    finally:
        x = True
except TypeError as te:
    y = True

await never()
""": ((2, 1, num_interactions_possible), {"x": True, "y": True}),


"""
from interaction import never

var x = False

def foo(x):    
    try:
        return x / 2
    finally:
        return x is not None

try:
    x = foo("hello")
except:
    x = False

await never()
""": ((2, 1, num_interactions_possible), {"x": True}),

"""
from interaction import never

var x = True

try:
    while True:
        try:
            raise Exception("This should not be re-raised, because the finally clause executes a break!")
        finally:
            break
except:
    x = False

await never()
""": ((2, 1, num_interactions_possible), {"x": True}),


"""
from interaction import never

var x = True

try:
    var i = 0
    while i < 3:
        try:
            i = i + 1
            raise Exception("This should not be re-raised, because the finally clause executes a continue!")
        finally:
            continue
except:
    x = False

await never()
""": ((2, 1, num_interactions_possible), {"x": True}),



"""
from interaction import never

var x = False

var i = 42

def increment():
    i = i + 1
    return i

def foo(x):    
    try:
        return increment()
    finally:
        i = 0

var r = foo()

await never()
""": ((2, 1, num_interactions_possible), {"r": 43, "i": 0}),

"""
from interaction import never

var x = False

while True:
    try:
        break
    finally:
        x = True

await never()
""": ((2, 1, num_interactions_possible), {"x": True}),


"""
from interaction import never

var i = 0
while i % 2 == 0 and i < 5 and i < 10:
    try:
        i = i + 1
        continue
    finally:
        i = i + 1

await never()
""": ((2, 1, num_interactions_possible), {"i": 10}),



"""
from interaction import never

def foo(x):    
    try:
        return False
    finally:
        return True

var x = foo(42)

await never()
""": ((2, 1, num_interactions_possible), {"x": True}),

}