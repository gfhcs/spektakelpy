# coding=utf8

from tkinter import *

from alpha import presentation
from alpha import behavior

if __name__ == '__main__':

    canvas = presentation.Canvas(1920, 1080)

    hello = canvas.add(presentation.Text("Hello", cx=0.5, cy=0.25, visible=False))
    world = canvas.add(presentation.Text("World", cx=0.5, cy=0.75, visible=False))

    canvas.behavior = """
        def appear_soft(widget):
            def a(widget):
                for _ in range(params.framerate):
                    after(1 / params.framerate)
                    widget.alpha += 0.1
            spawn(a(widget))
            
        def unfold():
            ?forward
            appear_soft(hello)
            ?forward
            appear_soft(world)
            
        def bounce():
            delta = 0.01
            while True:
                for _ in range(10):
                    after(0.1)
                    hello.cy += delta
                    world.cy += delta
                delta = - delta   
                
        unfold() | bounce()             
    """

    # canvas = presentation.flatten(canvas)

    presentation.present(canvas)
