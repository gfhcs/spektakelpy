from engine.core.interaction import num_interactions_possible

samples = {


"""
from interaction import never
var x = 42
if x % 2 == 0:
    x = "even"
var y = "done"

await never()
""": ((2, 1, num_interactions_possible), {"x": "even", "y": "done"}),

"""
from interaction import never
var x = 43
if x % 2 == 0:
    x = "even"
var y = "done"

await never()
""": ((2, 1, num_interactions_possible), {"x": 43, "y": "done"}),


"""
from interaction import never
var x = 42
if x % 2 == 0:
    x = "even"
else:
    x = "odd"
var y = "done"

await never()
""": ((2, 1, num_interactions_possible), {"x": "even", "y": "done"}),

"""
from interaction import never
var x = 43
if x % 2 == 0:
    x = "even"
else:
    x = "odd"
var y = "done"

await never()
""": ((2, 1, num_interactions_possible), {"x": "odd", "y": "done"}),

"""
from interaction import never
var x = 42
if x % 2 == 0:
    x = "even"
elif x == 1:
    x = "one"
else:
    x = "odd"
var y = "done"

await never()
""": ((2, 1, num_interactions_possible), {"x": "even", "y": "done"}),

"""
from interaction import never
var x = 43
if x % 2 == 0:
    x = "even"
elif x == 1:
    x = "one"
else:
    x = "odd"
var y = "done"

await never()
""": ((2, 1, num_interactions_possible), {"x": "odd", "y": "done"}),

"""
from interaction import never
var x = 1
if x % 2 == 0:
    x = "even"
elif x == 1:
    x = "one"
else:
    x = "odd"
var y = "done"

await never()
""": ((2, 1, num_interactions_possible), {"x": "one", "y": "done"}),



"""
from interaction import never
var x = 42
if x % 2 == 0:
    x = "even"
elif x == 1:
    x = "one"
elif x == 2:
    x = "two"
else:
    x = "odd"
var y = "done"

await never()
""": ((2, 1, num_interactions_possible), {"x": "even", "y": "done"}),

"""
from interaction import never
var x = 43
if x % 2 == 0:
    x = "even"
elif x == 1:
    x = "one"
elif x == 2:
    x = "two"
else:
    x = "odd"
var y = "done"

await never()
""": ((2, 1, num_interactions_possible), {"x": "odd", "y": "done"}),

"""
from interaction import never
var x = 1

if x % 2 == 0:
    x = "even"
elif x == 1:
    x = "one"
elif x == 2:
    x = "two"
else:
    x = "odd"
var y = "done"

await never()
""": ((2, 1, num_interactions_possible), {"x": "one", "y": "done"}),

"""
from interaction import never
var x = 3

if x % 2 == 0:
    x = "even"
elif x == 1:
    x = "one"
elif x == 3:
    x = "three"
else:
    x = "odd"
var y = "done"

await never()
""": ((2, 1, num_interactions_possible), {"x": "three", "y": "done"}),


}