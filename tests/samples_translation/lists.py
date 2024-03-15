from engine.core.interaction import num_interactions_possible
from engine.core.data import VIndexError

samples = {

# 0
"""
from interaction import never
var x = []
await never()
""": ((2, 1, num_interactions_possible), {"x": []}),

# 1
"""
from interaction import never
var x = [1]
await never()
""": ((2, 1, num_interactions_possible), {"x": [1]}),

# 2
"""
from interaction import never
var x = [1, 2, 3]
await never()
""": ((2, 1, num_interactions_possible), {"x": [1, 2, 3]}),

# 3
"""
from interaction import never
var x = list((1, 2, 3))
await never()
""": ((2, 1, num_interactions_possible), {"x": [1, 2, 3]}),

# 4
"""
from interaction import never
var x = isinstance([1, 2, 3], list)
await never()
""": ((2, 1, num_interactions_possible), {"x": True}),

# 5
"""
from interaction import never
var x = len([1, 2, 3])
await never()
""": ((2, 1, num_interactions_possible), {"x": 3}),

# 6
"""
from interaction import never
var x = [1, 2, 3][1]
await never()
""": ((2, 1, num_interactions_possible), {"x": 2}),

# 7
"""
from interaction import never
var x
try:
    x = [1, 2, 3][4]
except IndexError as iex:
    x = iex
await never()
""": ((2, 1, num_interactions_possible), {"x": VIndexError("list index out of range")}),

# 8
"""
from interaction import never
var x = [1, 2, 3]
x = (2 in x, 7 in x, 1 not in x, 42 not in x)
await never()
""": ((2, 1, num_interactions_possible), {"x": [True, False, False, True]}),

# 9
"""
from interaction import never
var x = [1, 2, 3]
x = x + x
await never()
""": ((2, 1, num_interactions_possible), {"x": [1, 2, 3, 1, 2, 3]}),

# 10
"""
from interaction import never
var x = [7] * 3
var y = 3 * [2]
await never()
""": ((2, 1, num_interactions_possible), {"x": [7, 7, 7], "y": [2, 2, 2]}),

# 11
"""
from interaction import never
var x, y, z = [1, 2, 3]
await never()
""": ((2, 1, num_interactions_possible), {"x": 1, "y": 2, "z": 3}),

# 12
"""
from interaction import never
var x = [1, 2, 3]
x[1] = x[1] + 1
await never()
""": ((2, 1, num_interactions_possible), {"x": [1, 3, 3]}),

# 13
"""
from interaction import never
var x = [1, 1]
while len(x) < 10:
    x.append(x[-2] + x[-1])
await never()
""": ((2, 1, num_interactions_possible), {"x": [1, 1, 2, 3, 5, 8, 13, 21, 34, 55]}),

# 14
"""
from interaction import never
var x = [1, 2, 3]
c.clear()
await never()
""": ((2, 1, num_interactions_possible), {"x": []}),

# 15
"""
from interaction import never
var x = [1, 2, 3]
x.extend((4, 5, 6))
await never()
""": ((2, 1, num_interactions_possible), {"x": [1, 2, 3, 4, 5, 6]}),

# 16
"""
from interaction import never
var x = [1, 3]
x.insert(1, 2)
await never()
""": ((2, 1, num_interactions_possible), {"x": [1, 2, 3]}),

# 17
"""
from interaction import never
var x = [1, 2, 3]
var y = x.pop((len(x))
await never()
""": ((2, 1, num_interactions_possible), {"x": [1, 2], "y": 3}),

# 18
"""
from interaction import never
var x = [1, 2, 3]
x.remove(2)
await never()
""": ((2, 1, num_interactions_possible), {"x": [1, 3]}),

# 19
"""
from interaction import never

# list.sort should stably sort in place. It should NOT take a key procedure, but assume that list elements
# are comparable. That's because we don't want list.sort to have to call stack procedures. A sort that does
# take a key procedure can of course be implemented on this basis.

var x = [3, 8, 3, 6, 80, 2, 5]
x.sort()
await never()
""": ((2, 1, num_interactions_possible), {"x": sorted([3, 8, 3, 6, 80, 2, 5])}),

}