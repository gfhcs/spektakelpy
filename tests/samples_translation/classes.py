samples = {


"""
from interaction import never

def foo():
    class C:
        pass

    def test():
        return C()

    return test

result = foo()()

await never()
""": ((2, 1, 3), {}),

}