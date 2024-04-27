from engine.core.interaction import num_interactions_possible


samples = {

# 0
"""
from interaction import never

class C:
    pass

var result = isinstance(C(), object)

await never()
""": ((2, 1,  num_interactions_possible), {"result": True}),

# 1
"""
from interaction import never

class Point:

    var _x, _y
    
    def __init__(self, x, y):
        self._x = x
        self._y = y
    
    def get_coordinates(self):
        return self._x, self._y

var result = Point(47, 11).get_coordinates()

await never()
""": ((2, 1,  num_interactions_possible), {"result": (47, 11)}),

# 2
"""
from interaction import never

class AbstractException(Exception):
    def __init__(self):
        super(AbstractException, self).__init__("This operation is abstract!")

var result = isinstance(AbstractException(), Exception)

await never()
""": ((2, 1, num_interactions_possible), {"result": True}),

# 3
"""
from interaction import never

class AbstractException(Exception):
    def __init__(self):
        super(AbstractException, self).__init__("This operation is abstract!")

class Shape:
    def get_area(self):
        raise AbstractException()
        
class Rectangle(Shape):
    var x, y, w, h
    def __init__(self, x, y, w, h):
        super(Rectangle, self).__init__()
        self.x, self.y, self.w, self.h = x, y, w, h
        
    def get_area(self):
        return self.w * self.h
        
class Circle(Shape):
    var x, y, r
    def __init__(self, x, y, r):
        super(Circle, self).__init__()
        self.x, self.y, self.r = x, y, r
        
    def get_area(self):
        return 3.1415926 * self.r ** 2

var r = Rectangle(0, 0, 4, 6)
var c = Circle(0.5, 0.5, 1 / 3.1415926 ** 0.5)

try:
    Shape().get_area()
    raise Exception("This should not work!")
except AbstractException:
    pass

var result = (r.get_area() == 4 * 6, c.get_area() == 3.1415926 * (1 / 3.1415926 ** 0.5) ** 2)

await never()
""": ((2, 1, num_interactions_possible), {"result": (True, True)}),

# 4
"""
from interaction import never

class Vehicle:    
    var _weight
    def __init__(self, weight):
        super(Vehicle, self).__init__()
        self._weight = weight

    def get_weight(self):
        return self._weight

class WheeledVehicle():
    var _num_wheels
    def __init__(self, num_wheels):
        self._num_wheels = num_wheels

    def get_num_wheels(self):
        return self._num_wheels

class WaterVehicle(Vehicle):
    var _draught
    def __init__(self, draught, weight):
        super(WaterVehicle, self).__init__(weight)
        self._draught = draught

    def get_draught(self):
        return self._draught
        
class AmphibiousVehicle(WheeledVehicle, WaterVehicle):
    def __init__(self, num_wheels, draught, weight):
        super(AmphibiousVehicle, self).__init__(num_wheels)
        super(WheeledVehicle, self).__init__(draught, weight)

var a = AmphibiousVehicle(3, 1, 1000)

var result = (a.get_num_wheels(), a.get_weight(), a.get_draught())

await never()
""": ((2, 1, num_interactions_possible), {"result": (3, 1000, 1)}),

# 5
"""
from interaction import never

def foo():
    class C:
        pass

    def test(self):
        return C()

    return test

var result = foo()()

await never()
""": ((2, 1,  num_interactions_possible), {}),

# 6
"""
from interaction import never

class C:    
    var x
    def __init__(self, x):
        self.x = x
        
var c = C(1337)
var a, b = False, False
try:
    c.x = 42
except AttributeError:
    a = True

try:
    b = c.x == 42
except AttributeError:
    b = True

await never()
""": ((2, 1, num_interactions_possible), {"a": True, "b": True}),

# 7
"""
from interaction import never

class DefaultingDict(dict):   
 
    var default
    
    def __init__(self, default):
        self.default = default
        
    def get_with_default(self, key):
        try:
            return self[key]
        except KeyError:
            return self.default

var d = DefaultingDict(42)
d[1] = 2

var result = (d.get_with_default(1), d.get_with_default(2))

await never()
""": ((2, 1, num_interactions_possible), {"result": (2, 42)}),

# 8
"""
from interaction import never

class C():

    def test(self):
        return 42

var result = C.test is C.test # Interestingly the equivalent for *instances* would not hold in Python!

await never()
""": ((2, 1, num_interactions_possible), {"result": True}),

# 9
"""
from interaction import never

class C():

    var b, i, f, s, d, l, r, t
    
    def __init__(self):
        self.b = True
        self.i = 42
        self.f = 42.0
        self.s = "Hello"
        self.d = {1: 2}
        self.l = [1, 2, 3]
        self.r = range(3)
        self.t = (1, 2, 3)

    def test(self):
        self.l.clear()
        return (not not self.b, self.i == self.f, self.s[2], self.d[1], list(self.r), list(self.t))

var result = C().test()

await never()
""": ((2, 1, num_interactions_possible), {"result": (True, True, "l", 2, [0, 1, 2], [1, 2, 3])}),

# 10
"""
from interaction import never

class A:

    var x

    def __init__(self, x):
        self.x = x

    def a(self):
        return self.x

class B(A):

    var x

    def __init__(self, x):
        super(B, self).__init__(x + 1)
        self.x = x

    def b(self):
        return self.x

var x = B(42)

var result = (x.a(), x.b())            

await never()
""": ((2, 1, num_interactions_possible), {"result": (43, 42)}),

# 11
"""
from interaction import never

class C:

    var x
    
    def __init__(self, x):
        self.x = x

    prop p:
        get(self):
            return self.x
            
var result = C(42).p
            
await never()
""": ((2, 1, num_interactions_possible), {"result": 42}),

# 12
"""
from interaction import never

class C:

    var x

    def __init__(self, x):
        self.x = x

    prop p:
        get(self):
            return self.x
            
class D(C):
    prop p:
        get(self):
            return super(D, self).p + 1

var result = D(42).p

await never()
""": ((2, 1, num_interactions_possible), {"result": 43}),

# 13
"""
from interaction import never

class C:

    var x

    def __init__(self, x):
        self.x = x

    prop p:
        get(self):
            return self.x
        set(self, value):
            self.x = value

var c = C(42)
c.p = c.p + 1

var result = c.p

await never()
""": ((2, 1, num_interactions_possible), {"result": 43}),

}