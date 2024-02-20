code = """
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
"""
