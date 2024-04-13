from engine.core.data import VRuntimeError
from engine.core.interaction import num_interactions_possible

samples = {

# 0
"""
from interaction import never
var l = []
for x in range(3):
    l.append(x)
await never()
""": ((2, 1, num_interactions_possible), {"l": [0, 1, 2]}),

# 1
"""
from interaction import never
var l = []
var i = iter(range(3))
while True:
    try:
        l.append(next(i))
    except StopIteration:
        break
await never()
""": ((2, 1, num_interactions_possible), {"l": [0, 1, 2]}),

# 2
"""
from interaction import never
var l = []
for x in range(3):
    def f(y):
        return x + y
    l.append(f)    
l = [l[0](42), l[1](42), l[2](42)]    
await never()
""": ((2, 1, num_interactions_possible), {"l": [44, 44, 44]}),

# 3
"""
from interaction import never
var l = []
for x in list(range(3)):
    l.append(x)
await never()
""": ((2, 1, num_interactions_possible), {"l": [0, 1, 2]}),

# 4
"""
from interaction import never
var l = []
for c in "Hello":
    l.append(c)
await never()
""": ((2, 1, num_interactions_possible), {"l": list("Hello")}),

# 5
"""
from interaction import never
var l = []
for x in tuple(range(3)):
    l.append(x)
await never()
""": ((2, 1, num_interactions_possible), {"l": [0, 1, 2]}),

# 6
"""
from interaction import never
var l = []
for k, v in {"Hello": 42, "Goodbye": 4711}.items():
    l.append((k, v))
await never()
""": ((2, 1, num_interactions_possible), {"l": [("Hello", 42), ("Goodbye", 4711)]}),

# 7
"""
from interaction import never

var primes = [2]

for i in range(100):
    if i <= 2:
        continue
        
    var prime = True
    for p in primes:
        if i % p == 0:
            prime = False
            break
            
    if prime:
        primes.append(i)

await never()
""": ((2, 1, num_interactions_possible), {"primes": [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97]}),


# 8
"""
from interaction import never
var l = [1, 2, 4]
try:
    for x in l:
        l.append(42)
except RuntimeError as rex:
    pass
await never()
""": ((2, 1, num_interactions_possible), {"rex": VRuntimeError("The iterable underlying this iterator has been modified!")}),


# 9
"""
from interaction import never
var d = {1: 2}
try:
    for k, v in d.items():
        d[42] = 42
except RuntimeError as rex:
    pass
await never()
""": ((2, 1, num_interactions_possible), {"rex": VRuntimeError("The iterable underlying this iterator has been modified!")}),


}