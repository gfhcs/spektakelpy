code = """  
from interaction import tick, never

var v = future()
var w = future()
var x = future()
var y = future()
var z = y

while v is not w:  
    await tick()
    v, w, x, y, z = w, x, y, z, v
    
await never()
"""
