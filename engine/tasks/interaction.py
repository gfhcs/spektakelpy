
from ..task import TaskState, TaskStatus
from ..machine import MachineState


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
        self._interaction = interaction

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
        return hash((self.taskid, self._interaction))

    def equals(self, other):
        return isinstance(other, InteractionState) \
               and self.taskid == other.taskid \
               and self._interaction == other._interaction \
               and self.status == other.status
