from engine.core.data import VBool
from lang.spek.data.builtin import builtin


@builtin("isinstance")
def builtin_isinstance(tstate, mstate, x, types):
    if not isinstance(types, tuple):
        types = (types, )
    t = x.type
    return VBool.from_bool(any(t.subtypeof(s) for s in types))
