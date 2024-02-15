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
from interaction import next

var fbe = None
def buffer_empty():
    if fbe is None or fbe.done:
        fbe = future()
    return fbe
    
var fbf = None
def buffer_full():
    if fbf is None or fbf.done:
        fbf = future()
    return fbf

var buffer = None

def produce():
    acc = 123
    while acc > 0:
        await next()
        await buffer_empty()
        buffer = acc % 10
        buffer_full().set(True)
        acc = acc // 10
    
var consumed = 0
def consume():
    while True:    
        await buffer_nonempty()
        consumed = 10 * consumed + buffer % 10
        buffer = None
        buffer_empty().set(True)
        
var c = async consume()
var p = async produce()

# The following never terminate:
await p
await c

""": ((11, 9, 6), {"consumed": 321, "buffer": None}),

}