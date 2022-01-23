


def explore(m, s):
    """
    Enumerates the entire state space of a task machine.
    :param m: The TaskMachine object the state space of which is to be explored.
    :param s: A Scheduler object that specifies which tasks are to be executed in which state.
    :return: An iterable of State objects.
    """

    # TODO: Careful, there will be loops.

    # TODO: There needs to be a scheduler that ensures that we never execute "external" actions while there
    #       still are *internal* actions possible.
    pass