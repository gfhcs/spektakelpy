
from engine.functional.values import VException, VTypeError
from engine.tasks.interaction import num_interactions_possible

samples = {

# 0
"""
from interaction import never

var x = False

var f = future()
f.cancel()

try:
    await f
except CancellationError:
    x = True

await never()
""": ((2, 1, num_interactions_possible), {"x": True}),


# 1
"""
from interaction import never

var x = True

var f = future()
f.exception = Exception("This is fun :-)")

try:
    await f
except CancellationError:
    x = False
except Exception as ex:
    x = ex

await never()
""": ((2, 1, num_interactions_possible), {"x": VException("This is fun :-)")}),


# 2
"""
from interaction import never, tick

var x, y = False, False

def foo():
    try:
        while True:
            await tick()
    except CancellationError:
        x = True
        raise

var t = async foo()

await tick()

t.cancel()

try:
    await t
except CancellationError:
    y = True

await never()
""": ((3, 2, 2 * num_interactions_possible), {"x": True, "y": True}),


# 3
"""
from interaction import never, tick

var x, y = False, False

def foo():
    try:
        while True:
            await tick()
            raise Exception("Crash!")
    finally:
        x = True

try:
    await async foo()
except Exception as ex:
    y = ex

await never()
""": ((3, 2, 2 * num_interactions_possible), {"x": True, "y": VException("Crash!")}),

}