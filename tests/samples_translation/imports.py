from engine.core.interaction import num_interactions_possible

samples = {

# 0
"""
from interaction import never
import a

var x = a.meaning

await never()
""": ((2, 1,  num_interactions_possible), {"x": 42}),

# 1
"""
import a as dussel
from interaction import never

var x = dussel.meaning

await never()
""": ((2, 1,  num_interactions_possible), {"x": 42}),

# 2
"""
from interaction import never
import test.test.b

var x = test.test.fun(42, 42)

await never()
""": ((2, 1,  num_interactions_possible), {"x": 42 + 42}),

# 3
"""
import test.test.b as b
from interaction import never

var x = b.fun(42, 42)

await never()
""": ((2, 1,  num_interactions_possible), {"x": 42 + 42}),

# 4
"""
from interaction import never
from a import meaning

var x = meaning + 1

await never()
""": ((2, 1,  num_interactions_possible), {"x": 43}),

# 5
"""
from a import meaning as fourtytwo
from interaction import never

var x = fourtytwo + 1

await never()
""": ((2, 1,  num_interactions_possible), {"x": 43}),

# 6
"""
from interaction import never
from a import meaning, answer

var x = (meaning + answer) // 2

await never()
""": ((2, 1,  num_interactions_possible), {"x": 42}),

# 7
"""
from a import meaning as number1, answer as number2
from interaction import never

var x = (number1 + number2) // 2

await never()
""": ((2, 1,  num_interactions_possible), {"x": 42}),

# 8
"""
from interaction import never
from c import TestClass as C
from test.test.b import fun

var c = C(21)

var x = fun(c.get_value(), 0)

await never()
""": ((2, 1,  num_interactions_possible), {"x": 42})

}