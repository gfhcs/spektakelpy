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
from interaction import next, never
var done = False
def foo():
    await next()
    done = True
await async foo()
await never()
""": ((6, 4, 6), {"done": True}),

"""
from interaction import never

var buffer = False

def produce():
    buffer = True

await async produce()
await never()

""": ((4, 3, 3), {"buffer": True}),


"""
from interaction import next, never

var buffer = None

def produce():
    var acc = 123
    while acc > 0:
        await next()
        buffer = acc % 10
        acc = acc // 10

var p = async produce()

await p
await never()

""": ((10, 6, 12), {"buffer": 1}),

"""
from interaction import next

var buffer = None
var fbe, fbf = None, None

def set_buffer(value):
    buffer = value
    if value is None and fbe is not None:
        fbe.result = True
        fbe = None
    if value is not None and fbf is not None:
        fbf.result = True
        fbf = None

def buffer_empty():
    var f = future()
    if buffer is None:
        f.result = True
    else:
        fbe = f     
    return f
    
def buffer_full():
    var f = future()
    if buffer is not None:
        f.result = True        
    else:
        fbf = f
    return f

def produce():
    var acc = 123
    while acc > 0:
        await next()
        await buffer_empty()
        set_buffer(acc % 10)
        acc = acc // 10
    
var consumed = 0
def consume():
    while True:    
        await buffer_full()
        consumed = 10 * consumed + buffer % 10
        set_buffer(None)

var c = async consume()
var p = async produce()

# The following never terminate:
await p
await c

""": ((14, 10, 12), {"consumed": 321, "buffer": None}),

}