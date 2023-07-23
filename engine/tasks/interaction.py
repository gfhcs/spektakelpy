from enum import Enum

from util import check_type
from util.immutable import check_sealed
from ..machine import MachineState
from ..task import TaskState, TaskStatus


class Interaction(Enum):
    """
    An enumeration of all the interaction labels that notify a spek program of outside events.
    """
    TICK = 0
    NEXT = 1
    PREV = 2


class BuiltinVariable(Enum):
    """
    Builtin variables.
    """
    TIME = 0


class InteractionState(TaskState):
    """
    Models a task that receives an Interaction. All this task does when executed is complete itself.
    """

    def __init__(self, interaction, taskid, status=TaskStatus.WAITING):
        """
        Initializes a new interaction state.
        :param interaction: An object that represents the type of interaction this task is waiting for.
        """
        super().__init__(taskid, status)
        self._interaction = check_type(interaction, Interaction)

    def clone_unsealed(self, clones=None):
        if clones is None:
            clones = {}
        try:
            return clones[id(self)]
        except KeyError:
            c = InteractionState(self._interaction, self.taskid, self.status)
            clones[id(self)] = c
            return c

    def _seal(self):
        pass

    @property
    def interaction(self):
        """
        An object that represent the type of interaction this task is waiting for.
        """
        return self._interaction

    def enabled(self, _):
        return True

    def run(self, mstate):
        task_states = list(mstate.task_states)
        task_states.remove(self)
        task_states.append(InteractionState(self.interaction, self.taskid, status=TaskStatus.COMPLETED))
        return MachineState(mstate.valuation, task_states)

    def hash(self):
        check_sealed(self)
        return hash((self.taskid, self.status, self._interaction))

    def equals(self, other):
        return isinstance(other, InteractionState) \
               and (self.taskid, self._interaction, self.status) == (other.taskid, other._interaction, other.status)

