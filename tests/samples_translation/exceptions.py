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

def foo(i):
    try:
        bar(i)
    except TypeError:
        x = True
        raise

def bar(i):
    try:
        return i % 2 == 0
    except AttributeError:
        return
    finally:
        y = True
    
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

# TODO:
#   If the finally clause executes a break, continue or return statement, exceptions are not re-raised.
#   If the try statement reaches a break, continue or return statement, the finally clause will execute just prior to the break, continue or return statement’s execution.
#   If a finally clause includes a return statement, the returned value will be the one from the finally clause’s return statement, not the value from the try clause’s return statement.

}