code = """
from interaction import never

def a(k, x1, x2, x3, x4, x5):
    def b():
        k = k - 1
        return a(k, b, x1, x2, x3, x4)
    if k <= 0:
        return x4() + x5()
    else:
        return b()

def one():
    return 1
def minusone():
    return -1
def zero():
    return 0

var result = a({k0}, one, minusone, minusone, one, zero)

await never()
"""
