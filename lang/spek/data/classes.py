from engine.core.atomic import EmptyMember
from engine.core.compound import CompoundType
from engine.stack.exceptions import VTypeError
from engine.stack.procedure import StackProcedure
from lang.spek.data.bound import BoundProcedure


class Class(CompoundType):
    """
    Represents a user-defined class.
    """

    def __init__(self, name, bases, direct_field_names, direct_members):
        """
        Creates a new class.
        :param name: The name of the class.
        :param bases: The Types this class is inheriting from.
        :param direct_field_names: The names of the direct fields of instances of this class.
        :param direct_members: A dict mapping member names to the direct (i.e. not inherited) members of this class.
        """
        super().__init__(name, bases, direct_field_names, direct_members)
        self._direct_field_names = direct_field_names

    @property
    def num_cargs(self):
        try:
            initializer = self.members["__init__"]
        except KeyError:
            return 0

        num_args = -1 # 'self' is not a constructor argument.
        while True:
            if isinstance(initializer, StackProcedure):
                num_args += initializer.num_args
                break
            elif isinstance(initializer, EmptyMember):
                # This represents the empty initializer, that takes only 'self' as argument:
                num_args += 1
                break
            elif isinstance(initializer, BoundProcedure):
                num_args -= sum(1 for v in initializer.bound if v is not None)
                initializer = initializer.core
            else:
                raise VTypeError(f"The number of constructor arguments for the class {self.name} cannot be determined!")

        assert num_args >= 0

        return num_args

    def clone_unsealed(self, clones=None):
        if clones is None:
            clones = {}
        try:
            return clones[id(self)]
        except KeyError:
            c = Class(self.name, tuple(b.clone_unsealed(clones) for b in self.bases), self._direct_field_names,
                      {n: m.clone_unsealed(clones) for n, m in self.direct_members.items()})
            clones[id(self)] = c
            return c
