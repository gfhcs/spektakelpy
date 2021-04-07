# coding=utf8

from tkinter import *

from alpha import presentation
from alpha import behavior

if __name__ == '__main__':

    canvas = presentation.Canvas(1920, 1080)

    hello = canvas.add(presentation.Text("Hello", cx=0.5, cy=0.25, visible=False))
    world = canvas.add(presentation.Text("World", cx=0.5, cy=0.75, visible=False))

    # TODO: We specify the behavior of processes by giving some procedures.
    #       These procedures are "executed statically", i.e. in some mode
    #       that allows us to construct state graphs. The processes recognize this mode
    #       and cooperate with the state graph construction.
    #       That's how, for example, property assignments do not perform the actual computation, but just
    #       record the action of updating the property value.

    def appear_smoothly(context, obj):
        def a():
            for _ in range(10):
                context.wait(0.1)
                obj.visible += 0.1

        context.spawn(a)

    def unfold(context):
        context.waitfor(presentation.Action.STEP)
        appear_smoothly(context, hello)
        context.waitfor(presentation.Action.STEP)
        appear_smoothly(context, world)

    def bounce(context):
        delta = context.var(0.01)
        while True:
            for _ in range(10):
                context.wait(0.1)
                hello.cy += delta
                world.cy += delta
            delta = - delta

    canvas.behavior = behavior.LambdaBehavior.concurrent(unfold, bounce)

    # canvas = presentation.flatten(canvas)

    presentation.present(canvas)
