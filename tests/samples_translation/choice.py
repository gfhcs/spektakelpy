code = """  
from interaction import next, prev, tick, never

var p1, p2 = next, prev

def choice(a, b):
    var f = future()
    var pa, pb
    def wait(x, value):
        await x()
        if not f.done:
            f.result = value
            if value == 0:
                pb.cancel()
            elif value == 1:
                pa.cancel()
    pa = async wait(a, 0)
    pb = async wait(b, 1)
    return f

def turn(idx):
    while (await choice(p1, p2)) != idx:
        pass
    var f = future()
    f.result = True
    return f
    
var s0, s1
def setstate(idx, step):
    if idx == 0:
        s0 = step
    elif idx == 1:
        s1 = step

def player(idx):
    while True:
        setstate(idx, False)
        await turn(idx)
        setstate(idx, True)
        await turn(idx)
                
var a = async player(0)
var b = async player(1)

await a
await b
await never
"""
