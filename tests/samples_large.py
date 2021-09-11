samples = [
"""

def max(x, y):
    if x >= y:
        return x
    else:
         return y
         
def max3(a, b, c):
    return max(a, max(b, c))

class A:

    def __init__(a, b, c):
        self._a = a
        self._b = b
        self._c = c
        
    prop largest:
        get:
            return max3(self._a, self._b, self._c)
            
class B(A):
    
    def __init__(a, b, c, d):
        super().__init__(a, b, c)
        self._d = d
        
    prop components:
        get:
            return (self._a, self._b, self._c, self._d)
        
    prop proper:
        get:
            d = self._d
            return self._a == d or self._b == d or self._c == d
    
b = B(1, 2, 3, 4)

while not b.proper:
    b._d = b._d - 1
    
print ("Done :-)")
            
"""
]