samples = {


"""
from interaction import never
var (x,) = (1,)
await never()
""": ((2, 1, 3), {"x": 1}),


"""
from interaction import never
var x, = 1,
await never()
""": ((2, 1, 3), {"x": 1}),


"""
from interaction import never
var x, y
x = 1
y = 2
await never()
""": ((2, 1, 3), {"x": 1, "y": 2}),

"""
from interaction import never
var x, y
x, y = (1, 2)
await never()
""": ((2, 1, 3), {"x": 1, "y": 2}),


"""
from interaction import never
var x, y = (1, 2)
await never()
""": ((2, 1, 3), {"x": 1, "y": 2}),

"""
from interaction import never
var x, y = 1, 2
await never()
""": ((2, 1, 3), {"x": 1, "y": 2}),


"""
from interaction import never
var x, y, z = (1, 2, 3)
await never()
""": ((2, 1, 3), {"x": 1, "y": 2, "z": 3}),

"""
from interaction import never
var (x, (y, z)) = (1, (2, 3))
await never()
""": ((2, 1, 3), {"x": 1, "y": 2, "z": 3}),

"""
from interaction import never
var (((x, y), z), )
(((x, y), z), ) = (((1, 2), 3), )
await never()
""": ((2, 1, 3), {"x": 1, "y": 2, "z": 3}),

}