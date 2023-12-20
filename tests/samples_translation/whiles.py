samples = {

"""
from interaction import never

var x = 0
while x < 10:
    x = x + 1

await never()
""": ((2, 1, 3), {"x": 10}),


"""
from interaction import never

var x = 1
while x < 0:
    x = x + 1

await never()
""": ((2, 1, 3), {"x": 1}),


"""
from interaction import never

var x = 0
while x < 10:

    if x % 2 == 0:
        x = x + 3
        continue

    x = x + 1

await never()
""": ((2, 1, 3), {"x": 11}),

"""
from interaction import never

var x = 1
while x < 10:

    if x % 2 == 0:
        break

    x = x + 1

await never()
""": ((2, 1, 3), {"x": 2}),


}