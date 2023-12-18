samples = {


"""
from interaction import never
var x = 42
if x % 2 == 0:
    x = "even"

await never()
""": ((2, 1, 3), {"x": "even"}),

"""
from interaction import never
var x = 43
if x % 2 == 0:
    x = "even"

await never()
""": ((2, 1, 3), {"x": 43}),


"""
from interaction import never
var x = 42
if x % 2 == 0:
    x = "even"
else:
    x = "odd"

await never()
""": ((2, 1, 3), {"x": "even"}),

"""
from interaction import never
var x = 43
if x % 2 == 0:
    x = "even"
else:
    x = "odd"

await never()
""": ((2, 1, 3), {"x": "odd"}),

"""
from interaction import never
var x = 42
if x % 2 == 0:
    x = "even"
elif x == 1:
    x = "one"
else:
    x = "odd"

await never()
""": ((2, 1, 3), {"x": "even"}),

"""
from interaction import never
var x = 43
if x % 2 == 0:
    x = "even"
elif x == 1:
    x = "one"
else:
    x = "odd"

await never()
""": ((2, 1, 3), {"x": "odd"}),

"""
from interaction import never
var x = 1
if x % 2 == 0:
    x = "even"
elif x == 1:
    x = "one"
else:
    x = "odd"

await never()
""": ((2, 1, 3), {"x": "one"}),



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

await never()
""": ((2, 1, 3), {"x": "even"}),

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

await never()
""": ((2, 1, 3), {"x": "odd"}),

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

await never()
""": ((2, 1, 3), {"x": "one"}),

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

await never()
""": ((2, 1, 3), {"x": "three"}),


}