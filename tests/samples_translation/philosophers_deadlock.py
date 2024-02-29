code = """  
from interaction import next, prev, resume, never

var p1, p2, p3 = next, prev, resume

def turn(idx):
    if idx == 0:
        return p1()
    elif idx == 1:
        return p2()
    elif idx == 2:
        return p3()

var f1 = None
def get_s1():
    if f1 is None:
        f1 = future()
        var spoon = future()
        spoon.result = True
        return spoon
    else:
        return f1
def put_s1():
    f1.result = True
    f1 = None

var f2 = None
def get_s2():
    if f2 is None:
        f2 = future()
        var spoon = future()
        spoon.result = True
        return spoon
    else:
        return f2
def put_s2():
    f2.result = True
    f2 = None
    
var f3 = None
def get_s3():
    if f3 is None:
        f3 = future()
        var spoon = future()
        spoon.result = True
        return spoon
    else:
        return f3
def put_s3():
    f3.result = True
    f3 = None
    
    
var s0, s1, s2 = "", "", ""
def setstate(idx, step):
    if idx == 0:
        s0 = step
    elif idx == 1:
        s1 = step
    elif idx == 2:
        s2 = step

def philosopher(idx, get_left, put_left, get_right, put_right):
    while True:
        setstate(idx, "")
        await turn(idx)
        setstate(idx, "awaiting_left")
        await get_left()
        setstate(idx, "has_left")
        await turn(idx)
        setstate(idx, "awaiting_right")
        await get_right()
        setstate(idx, "eating")
        await turn(idx)
        put_left()
        setstate(idx, "has_right")
        await turn(idx)
        put_right()
                
var a = async philosopher(0, get_s3, put_s3, get_s1, put_s1)
var b = async philosopher(1, get_s1, put_s1, get_s2, put_s2)
var c = async philosopher(2, get_s2, put_s2, get_s3, put_s3)

await a
await b
await c
await never()
"""
