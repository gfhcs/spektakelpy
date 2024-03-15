from engine.core.data import VIndexError
from engine.core.interaction import num_interactions_possible


samples = {

# 0
"""
from interaction import never
var x = ()
await never()
""": ((2, 1, num_interactions_possible), {"x": ()}),

# 1
"""
from interaction import never
var x = (1,)
await never()
""": ((2, 1, num_interactions_possible), {"x": (1,)}),

# 2
"""
from interaction import never
var x = (1, 2, 3)
await never()
""": ((2, 1, num_interactions_possible), {"x": (1, 2, 3)}),

# 3
"""
from interaction import never
var x = tuple((1, 2, 3))
await never()
""": ((2, 1, num_interactions_possible), {"x": (1, 2, 3)}),

# 4
"""
from interaction import never
var x = isinstance((1, 2, 3), tuple)
await never()
""": ((2, 1, num_interactions_possible), {"x": True}),

# 5
"""
from interaction import never
var x = len((1, 2, 3))
await never()
""": ((2, 1, num_interactions_possible), {"x": 3}),

# 6
"""
from interaction import never
var x = (1, 2, 3)[1]
await never()
""": ((2, 1, num_interactions_possible), {"x": 2}),

# 7
"""
from interaction import never
var x
try:
    x = (1, 2, 3)[4]
except IndexError as iex:
    x = iex
await never()
""": ((2, 1, num_interactions_possible), {"x": VIndexError("tuple index out of range")}),

# 8
"""
from interaction import never
var x = (1, 2, 3)
x = (2 in x, 7 in x, 1 not in x, 42 not in x)
await never()
""": ((2, 1, num_interactions_possible), {"x": (True, False, False, True)}),

# 9
"""
from interaction import never
var x = (1, 2, 3)
x = x + x
await never()
""": ((2, 1, num_interactions_possible), {"x": (1, 2, 3, 1, 2, 3)}),

# 10
"""
from interaction import never
var x = (7, ) * 3
var y = 3 * (2, )
await never()
""": ((2, 1, num_interactions_possible), {"x": (7, 7, 7), "y": (2, 2, 2)}),

# 11
"""
from interaction import never
var x = (1, 2, 3)
x = x == (1, 2, 3)
await never()
""": ((2, 1, num_interactions_possible), {"x": True}),

# 12
"""
from interaction import never
var x = (1, 2, 3)
x = x != (7, 7, 7)
await never()
""": ((2, 1, num_interactions_possible), {"x": True}),

# 13
"""
from interaction import never
var x = (1, 2, (3, 3))
x = (3, 3) in x
await never()
""": ((2, 1, num_interactions_possible), {"x": True}),

# 14
"""
from interaction import never
var x = (object(), object()) == (object(), object())
await never()
""": ((2, 1, num_interactions_possible), {"x": False}),

# 15
"""
from interaction import never
var x = (future(), future()) == (future(), future())
await never()
""": ((2, 1, num_interactions_possible), {"x": False}),

# 16
"""
from interaction import never
var x, y, z = (1, 2, 3)
await never()
""": ((2, 1, num_interactions_possible), {"x": 1, "y": 2, "z": 3}),

}