from enum import Enum

from util import check_type
from util.immutable import check_sealed
from ..machine import MachineState
from ..task import TaskState, TaskStatus


class Interaction(Enum):
    """
    An enumeration of all the interaction labels that notify a spek program of outside events.
    """
    NEVER = -1
    TICK = 0
    NEXT = 1
    PREV = 2


def i2s(i):
    """
    Formats an interaction label as a string.
    :param i: An Interaction value.
    :return: A string.
    """
    r = str(i)
    return r[r.index(".") + 1:]


class BuiltinVariable(Enum):
    """
    Builtin variables.
    """
    TIME = 0


class InteractionState(TaskState):
    """
    Models a task that receives an Interaction. All this task does when executed is complete itself.
    """

    def __init__(self, interaction, status=TaskStatus.WAITING):
        """
        Initializes a new interaction state.
        :param interaction: An object that represents the type of interaction this task is waiting for.
        """
        super().__init__(status)
        self._interaction = check_type(interaction, Interaction)

    def print(self, out):
        status = "RECEIVED" if self.status == TaskStatus.COMPLETED else "Waiting for"
        out.write(f"InteractionState({status} {i2s(self._interaction)})")

    def clone_unsealed(self, clones=None):
        if clones is None:
            clones = {}
        try:
            return clones[id(self)]
        except KeyError:
            c = InteractionState(self._interaction, self.status)
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
        return self.status == TaskStatus.WAITING

    def run(self, mstate):
        if not self.enabled(mstate):
            return
        self.status = TaskStatus.COMPLETED
        for idx, t in enumerate(mstate.task_states):
            if t is self:
                mstate.remove_task(idx)
                mstate.add_task(InteractionState(self.interaction, status=TaskStatus.WAITING), index=idx)
                break

    def hash(self):
        check_sealed(self)
        return hash((self.status, self._interaction))

    def equals(self, other):
        return isinstance(other, InteractionState) \
               and (self._interaction, self.status) == (other._interaction, other.status)

