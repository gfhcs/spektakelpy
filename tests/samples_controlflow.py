from lang.spek import ast

samples = {
"""
atomic:
    h = x
    x = y
    y = h
""": ast.AtomicBlock,

"""
if e == m * c ** 2:
    return True
""": ast.Conditional,

"""
if a ** 2 + b ** 2 == c ** 2:
    return True
else:
    panic()
""": ast.Conditional,

"""
if x == "hello":
    return True
elif x == "world":
    return False
""": ast.Conditional,

"""
if x in words:
    if x == 42:
        k = k + 1
        return True
    elif x == 4711:
        k = k + 2
        return False
    elif x == 1337:
        k = 0
        return False
    elif x == "dussel":
        crash(x)
    else:
        print("Did not work!")
""": ast.Conditional,

"""
while energy < 100:
    energy = energy + sleep(energy)
print("Good morning :-)")    
""": None,

"""
while True:
    atomic:
        if locked:
            continue
        else:
            locked = True
            break
do_stuff()
locked = False
""": None,

"""
for x in xs:
    if x > 0:
        return False
return True
""": None,

"""
for x, y in zip(xs, ys):
    if x < y:
        return False
return True
""": None,

"""
try:
    e = m * c ** 2
finally:
    print("All is relative!")
""": ast.Try,

"""
try:
    work()
except:
    print("Sorry!")
""": ast.Try,

"""
try:
    work()
except ValueError:
    print("Sorry!")
""": ast.Try,

"""
try:
    work()
except ValueError as ve:
    print("Sorry!")
""": ast.Try,

"""
try:
    work()
except ValueError:
    print("Sorry!")
except RuntimeError as re:
    print("RuntimeError!")
except:
    print("Unknown error!")
finally:
    print("Done.")
""": ast.Try,
}
