from engine.tasks.interaction import num_interactions_possible

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
""": ((4, 3, num_interactions_possible), {"result": 42, "done": True}),

"""
var f = future()
await f
""": ((2, 1, num_interactions_possible), {}),

"""
from interaction import never
var f = future()
f.result = 42
var result = await f
await never()
""": ((2, 1, num_interactions_possible), {"result": 42}),

"""
from interaction import next, never
var done = False
await next()
done = True
await never()
""": ((4, 2, 2 * num_interactions_possible), {"done": True}),

"""
from interaction import next, never
var done = False
def foo():
    await next()
    done = True
await async foo()
await never()
""": ((6, 4, 2 * num_interactions_possible), {"done": True}),

"""
from interaction import never

var buffer = False

def produce():
    buffer = True

await async produce()
await never()

""": ((4, 3, num_interactions_possible), {"buffer": True}),


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

""": ((10, 6, 4 * num_interactions_possible), {"buffer": 1}),

}