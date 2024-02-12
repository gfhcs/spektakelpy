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


}