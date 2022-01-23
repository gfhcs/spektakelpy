from tkinter import *
import time
from legacy.core.events import TickEvent, ForwardEvent, BackwardEvent


def render(canvas, s):
    """
    Renders the state of a spectacle on a TkInter canvas.
    :param canvas: The TkInter canvas to render on.
    :param s: The state of a spectacle.
    """
    raise NotImplementedError("Rendering of spectacle state has not been implemented yet!")


def present(s):
    """
    Presents a spectacle live on screen.
    :param s: A Spectacle object that is to be presented.
    """

    c, state = s.initial_location, s.initial_state
    t0 = time.time()
    tprev = time.time()
    w, h = 1920, 1080
    fps = 30

    root = Tk()

    def on_key(e):
        if e.char in [" \n"]:
            raise_event(ForwardEvent())

    def on_left(e):
        raise_event(BackwardEvent())

    def on_right(e):
        raise_event(ForwardEvent())

    def on_refresh():
        nonlocal tprev, canvas, state
        t = time.time()
        d = t - tprev
        tprev = t
        root.after(1000.0 / fps, on_refresh)
        raise_event(TickEvent(delta=d))
        render(canvas, state)

    def raise_event(e):
        """
        Triggers an event in the spectacle, i.e. follows the relevant edge for this event, based on the current
        control location and the current state, as well as the event arguments.
        :param e: The Event object to raise.
        """
        raise NotImplementedError("Raising events in a spectacle has not been implemented yet!")

    root.geometry("{w}x{h}".format(w=w, h=h))
    frame = Frame(root)

    frame.bind("<KeyPress>", on_key)
    frame.bind("<Left>", on_left)
    frame.bind("<Right>", on_right)
    frame.pack()

    canvas = Canvas(root, width=w, height=h)
    canvas.pack()

    root.title("Presentation")
    root.after(0, on_refresh())
    root.mainloop()