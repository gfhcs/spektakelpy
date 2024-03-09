from engine.core.interaction import num_interactions_possible

samples = {

"""
from interaction import never

def foo(x):
    def bar(y):
        return x + y
    return bar

var result = foo(42)(1)

await never()
""": ((2, 1, num_interactions_possible), {"result": 43}),


"""
from interaction import never

var acc = 0

def foo(x):
    def bar():
        acc = 10 * acc + x
    def zoo():
        x = x + 1
    return bar, zoo

var b, z = foo(1)
b()
z()
b()

await never()
""": ((2, 1, num_interactions_possible), {"acc": 12}),

"""
from interaction import never

var foo1, foo2, foo3
var x = 1
var acc = 0

while x <= 3:
    def foo():
        acc = 10 * acc + x
    if x == 1:
        foo1 = foo
    elif x == 2:
        foo2 = foo
    elif x == 3:
        foo3 = foo
    x = x + 1

foo1()
foo2()
foo3()

await never()
""": ((2, 1, num_interactions_possible), {"acc": 444}),

"""
from interaction import never

var flag = True

def foo():
    return never()

await foo()
flag = False

""": ((2, 1, num_interactions_possible), {"flag": True}),

}