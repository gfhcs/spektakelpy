from engine.core.interaction import num_interactions_possible
from engine.core.data import VIndexError

samples = {

# 0
"""
from interaction import never
var x = ""
await never()
""": ((2, 1, num_interactions_possible), {"x": ""}),

# 1
"""
from interaction import never
var x = "Hello world"
await never()
""": ((2, 1, num_interactions_possible), {"x": "Hello world"}),

# 2
"""
from interaction import never
var x = str("Hello")
var y = str(42)
var z = str(42.0)
await never()
""": ((2, 1, num_interactions_possible), {"x": "Hello", "y": "42", "z": "42.0"}),

# 3
"""
from interaction import never
var x = isinstance("Hello", str)
await never()
""": ((2, 1, num_interactions_possible), {"x": True}),

# 4
"""
from interaction import never
var x = len("Hello world")
await never()
""": ((2, 1, num_interactions_possible), {"x": 11}),

# 5
"""
from interaction import never
var x = "Hello"[1]
await never()
""": ((2, 1, num_interactions_possible), {"x": "e"}),

# 6
"""
from interaction import never
var x
try:
    x = "abc"[4]
except IndexError as iex:
    x = iex
await never()
""": ((2, 1, num_interactions_possible), {"x": VIndexError("string index out of range")}),

# 7
"""
from interaction import never
var x = "Hello"
x = ("e" in x, "a" in x, "h" not in x, "a" not in x, "ll" in x)
await never()
""": ((2, 1, num_interactions_possible), {"x": (True, False, False, True, True)}),

# 8
"""
from interaction import never
var x = "Otto"
x = x + x
await never()
""": ((2, 1, num_interactions_possible), {"x": "OttoOtto"}),

# 9
"""
from interaction import never
var x = "abc" * 3
var y = 2 * "Otto"
await never()
""": ((2, 1, num_interactions_possible), {"x": "abcabcabc", "y": "OttoOtto"}),

# 10
"""
from interaction import never
var x = "Test"
x = x == "Test"
await never()
""": ((2, 1, num_interactions_possible), {"x": True}),

# 11
"""
from interaction import never
var x = "Test"
x = x != "Hello"
await never()
""": ((2, 1, num_interactions_possible), {"x": True}),

}