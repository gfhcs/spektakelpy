from engine.core.interaction import num_interactions_possible
from engine.core.data import VIndexError

samples = {


# 0
"""
from interaction import never
var x = isinstance(range, type)
await never()
""": ((2, 1, num_interactions_possible), {"x": True}),

# 1
"""
from interaction import never
var x = list(range(0))
await never()
""": ((2, 1, num_interactions_possible), {"x": []}),

# 2
"""
from interaction import never
var x = list(range(1))
await never()
""": ((2, 1, num_interactions_possible), {"x": [0]}),

# 3
"""
from interaction import never
var x = list(range(3))
await never()
""": ((2, 1, num_interactions_possible), {"x": [0, 1, 2]}),

# 4
"""
from interaction import never
var x = isinstance(range(3), range)
await never()
""": ((2, 1, num_interactions_possible), {"x": True}),

# 5
"""
from interaction import never
var x = len(range(3))
await never()
""": ((2, 1, num_interactions_possible), {"x": 3}),

# 6
"""
from interaction import never
var x = range(3)[1]
await never()
""": ((2, 1, num_interactions_possible), {"x": 1}),

# 7
"""
from interaction import never
var x
try:
    x = range(3)[4]
except IndexError as iex:
    x = iex
await never()
""": ((2, 1, num_interactions_possible), {"x": VIndexError("range object index out of range")}),

# 8
"""
from interaction import never
var x = range(3)
x = [2 in x, 7 in x, 1 not in x, 42 not in x]
await never()
""": ((2, 1, num_interactions_possible), {"x": [True, False, False, True]}),

# 9
"""
from interaction import never
var x, y, z = range(3)
await never()
""": ((2, 1, num_interactions_possible), {"x": 0, "y": 1, "z": 2}),

# 10
"""
from interaction import never
var x = range(3) == range(3)
await never()
""": ((2, 1, num_interactions_possible), {"x": True}),

}