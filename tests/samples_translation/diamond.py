code = """
from interaction import next, prev

var n = 2

def count(n, i):
    var c = 0
    while True:
        await i()
        c = (c + 1) % n

var c1, c2 = async count(n, next), async count(n, prev)

# These never terminate:
await c1
await c2

"""
