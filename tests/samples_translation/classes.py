from engine.core.interaction import num_interactions_possible

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
""": ((2, 1,  num_interactions_possible), {}),

}