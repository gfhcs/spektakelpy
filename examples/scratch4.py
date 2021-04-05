# coding=utf8

from tkinter import *

if __name__ == '__main__':

    canvas = Canvas(1920, 1080)

    hello = canvas.add(Text("Hello", cx=0.5, cy=0.25, visible=False))
    world = canvas.add(Text("World", cx=0.5, cy=0.75, visible=False))

    def animate():
        canvas.waitfor(next)
        hello.visible = True
        canvas.waitfor(next)
        world.visible = True

    canvas.behavior = animate

    present(canvas)