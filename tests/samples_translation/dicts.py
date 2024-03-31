from engine.core.interaction import num_interactions_possible
from engine.core.data import VIndexError, VKeyError

samples = {

# 0
"""
from interaction import never
var x = {}
await never()
""": ((2, 1, num_interactions_possible), {"x": {}}),

# 1
"""
from interaction import never
var x = {"hello": 42}
await never()
""": ((2, 1, num_interactions_possible), {"x": {"hello": 42}}),

# 2
"""
from interaction import never
var x = {1: 2, 2: 3, 3: 4}
await never()
""": ((2, 1, num_interactions_possible), {"x": {1: 2, 2: 3, 3: 4}}),

# 3
"""
from interaction import never
var x = dict({1: 2, 2: 3, 3: 4})
await never()
""": ((2, 1, num_interactions_possible), {"x": {1: 2, 2: 3, 3: 4}}),

# 4
"""
from interaction import never
var x = isinstance({1: 2, 2: 3, 3: 4}, dict)
await never()
""": ((2, 1, num_interactions_possible), {"x": True}),

# 5
"""
from interaction import never
var x = len({1: 2, 2: 3, 3: 4})
await never()
""": ((2, 1, num_interactions_possible), {"x": 3}),

# 6
"""
from interaction import never
var x = {1: 2, 2: 3, 3: 4}[2]
await never()
""": ((2, 1, num_interactions_possible), {"x": 3}),

# 7
"""
from interaction import never
var x
try:
    x = {1: 2, 2: 3, 3: 4}[4]
except KeyError as kex:
    x = kex
await never()
""": ((2, 1, num_interactions_possible), {"x": VKeyError("KeyError: 4")}),

# 8
"""
from interaction import never
var x = {1: 2, 2: 3, 3: 4}
x = [2 in x, 7 in x, 1 not in x, 42 not in x]
await never()
""": ((2, 1, num_interactions_possible), {"x": [True, False, False, True]}),

# 9
"""
from interaction import never
var x = {1: 2, 2: 3, 3: 4}
x[1] = x[1] + 1
await never()
""": ((2, 1, num_interactions_possible), {"x": {1: 3, 2: 3, 3: 4}}),

# 10
"""
from interaction import never
var x = {0: 1, 1: 1}
while len(x) < 10:
    x[len(x)] = x[len(x) - 2] + x[len(x) - 1]
await never()
""": ((2, 1, num_interactions_possible), {"x": {0: 1, 1: 1, 2: 2, 3: 3, 4: 5, 5: 8, 6: 13, 7: 21, 8: 34, 9: 55}}),

# 11
"""
from interaction import never
var x = {1: 2, 2: 3, 3: 4}
x.clear()
await never()
""": ((2, 1, num_interactions_possible), {"x": {}}),

# 12
"""
from interaction import never
var x = {1: 2, 2: 3, 3: 4}
x.update({{1: 2, 4: 5}})
await never()
""": ((2, 1, num_interactions_possible), {"x": {1: 2, 2: 3, 3: 4, 4: 5}}),

# 13
"""
from interaction import never
var x = {1: 2, 2: 3, 3: 4}
var y = x.pop(2)
await never()
""": ((2, 1, num_interactions_possible), {"x": {1: 2, 3: 4}, "y": 3}),

# 14
"""
from interaction import never
var x = dict([(1, 2), (2, 3), (3, 4)])
await never()
""": ((2, 1, num_interactions_possible), {"x": {1: 2, 2: 3, 3: 4}}),

# 15
"""
from interaction import never
var x = list(dict([(1, 2), (2, 3), (3, 4)]))
await never()
""": ((2, 1, num_interactions_possible), {"x": [1, 2, 3]}),

# 16
"""
from interaction import never
var x = list(dict([(1, 2), (2, 3), (3, 4)]).items())
await never()
""": ((2, 1, num_interactions_possible), {"x": [(1, 2), (2, 3), (3, 4)]}),

}