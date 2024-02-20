samples = {

"""
from interaction import never


var done = False

def work():
    done = True
    return 42
    
var task = async work()
    
var result
    
if done:
    result = -1

result = await task
    
await never()
""": ((4, 3, 3), {"result": 42, "done": True}),

"""
var f = future()
await f
""": ((2, 1, 3), {}),

"""
from interaction import never
var f = future()
f.result = 42
var result = await f
await never()
""": ((2, 1, 3), {"result": 42}),

"""
from interaction import next, never
var done = False
await next()
done = True
await never()
""": ((4, 2, 6), {"done": True}),

"""
from interaction import next

var buffer = None

var fbe = None
def buffer_empty():
    if fbe is None or fbe.done:
        fbe = future()
        if buffer is None:
            fbe.result = True
    return fbe
    
var fbf = None
def buffer_full():
    if fbf is None or fbf.done:
        fbf = future()
        if buffer is not None:
            fbf.result = True
    return fbf


def produce():
    var acc = 123
    while acc > 0:
        await next()
        await buffer_empty()
        buffer = acc % 10
        buffer_full().result = True
        acc = acc // 10
    
var consumed = 0
def consume():
    while True:    
        await buffer_full()
        consumed = 10 * consumed + buffer % 10
        buffer = None
        buffer_empty().result = True
        
var c = async consume()
var p = async produce()

# The following never terminate:
await p
await c

""": ((14, 10, 12), {"consumed": 321, "buffer": None}),

}