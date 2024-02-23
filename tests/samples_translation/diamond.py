code = """
from interaction import next, prev

var n = 2
var state = 0

def count(n, i, sidx):
    var c = 0
    while True:
        await i()
        state = state - ((state // 10 ** sidx) % 10) * 10 ** sidx
        c = (c + 1) % n
        state = state + c * 10 ** sidx

var c1, c2 = async count(n, next, 1), async count(n, prev, 0)

# These never terminate:
await c1
await c2

"""
