code = """  
from interaction import tick, never

var x = future()
var y = future()
var z = y

var counter = 0
while counter < 1 or z is not y:
    await tick()
    x, y = y, x
    counter = (counter + 1) % 2
    
await never()
"""
