code = """  
from interaction import next, prev, tick, never

var p1, p2 = next, prev
var free = True
def begin_turn(idx):
    var p
    if idx == 0:
        p = p1
    else:
        p = p2
    var c = None
    while c is None or not free:
        c = p()
        await c
    free = False
    return c      
            
def end_turn():
    await tick()
    free = True
    
var s0, s1
def setstate(idx, step):
    if idx == 0:
        s0 = step
    elif idx == 1:
        s1 = step

def player(idx):
    while True:
        setstate(idx, False)
        await begin_turn(idx)
        setstate(idx, True)
        await end_turn()
                
var a = async player(0)
var b = async player(1)

await a
await b
await never
"""
