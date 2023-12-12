
samples = {
"""
from interaction import never
var x = True
var y = False
await never()
""": ((2, 1, 3), {"x": True, "y": False}),
"""
from interaction import never
var x = "Hello world"
await never()
""": ((2, 1, 3), {"x": "Hello world"}),
"""
from interaction import never
var x = None
await never()
""": ((2, 1, 3), {"x": None}),
"""
from interaction import never
var x = 42
var y = 3.1415926
await never()
""": ((2, 1, 3), {"x": 42, "y": 3.1415926}),
"""
from interaction import never
var x = 42
var y = x
await never()
""": ((2, 1, 3), {"y": 42})
}