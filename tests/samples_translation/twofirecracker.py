code = """  
from interaction import next, prev, tick, resume

var strike, bang, extinguish, go_on = next, prev, tick, resume

var state = 0

var laf, lpf = future(), future()

def light_active():
    var f = lpf
    await go_on()
    if f is lpf:
        laf.result = True
        await lpf
        lpf = future()
    
def light_passive():
    await laf
    lpf.result = True
    laf = future()

def choice(a, b):
    var f = future()
    def wait(x, value):
        await x
        if not f.done:
            f.result = value  
    async wait(a, True)
    async wait(b, False)            
    return f

def match():        
    await strike()
    state = 6
    while await choice(async light_active(), extinguish()):
        state = 7
    lpf = future()
    if state == 7:
        state = 4
    elif state == 3:
        state = 5
    else:
        state = 2
    
def two_firecracker():
    await async light_passive()
    state = 7
    await bang()
    if state == 7:
        state = 3
    elif state == 4:
        state = 5
    await bang()
    if state == 3:
        state = 1
    elif state == 5:
        state = 2

var m = async match()
var c = async two_firecracker()

await m
await c
"""
