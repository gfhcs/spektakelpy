from engine.tasks.interaction import num_interactions_possible

samples = {
"""
from interaction import never
var x = True
var y = False
await never()
""": ((2, 1, num_interactions_possible), {"x": True, "y": False}),
"""
from interaction import never
var x = "Hello world"
await never()
""": ((2, 1, num_interactions_possible), {"x": "Hello world"}),
"""
from interaction import never
var x = None
await never()
""": ((2, 1, num_interactions_possible), {"x": None}),
"""
from interaction import never
var x = 42
var y = 3.1415926
await never()
""": ((2, 1, num_interactions_possible), {"x": 42, "y": 3.1415926}),
"""
from interaction import never
var x = 42
var y = x
await never()
""": ((2, 1, num_interactions_possible), {"y": 42}),
"""
from interaction import never
var x = 42
var y = -x
var z = not True
await never()
""": ((2, 1, num_interactions_possible), {"y": -42, "z": False}),
"""
from interaction import never
var x = 42
var y = 4711
var z = 1
z = (2 * x + 13 * y - (x + y) ** 2) // 2
var a = z // 7 - z / 7
var b = z / 216745647
await never()
""": ((2, 1, num_interactions_possible), {"z": -11264841, "a": 0.0, "b": -0.05197262854372342}),
"""
from interaction import never
var x = 42
var y = 4711
var z = 1
var a = (x * z) == x and x != z
var b = y != x and y != y
var c = y < x or False
var d = not z <= 5
var e = y > z
var f = x <= y
var g = None is None
var h = None is not None
await never()
""": ((2, 1, num_interactions_possible), {"a": True, "b": False, "c": False, "d": False, "e": True, "f": True, "g": True, "h": False})
}