# coding=utf8

from tkinter import *

from alpha import presentation

if __name__ == '__main__':

    canvas = presentation.Canvas(1920, 1080)

    hello = canvas.add(presentation.Text("Hello", cx=0.5, cy=0.25, visible=False))
    world = canvas.add(presentation.Text("World", cx=0.5, cy=0.75, visible=False))

    appear_soft = """
        offer appear;
        appear;
        for _ in range(params.framerate):
            wait 1 / params.framerate;
            self.alpha += 0.1;
    """

    hello.behavior += appear_soft
    world.behavior += appear_soft

    canvas.behavior = """
        offer forward
            
        def unfold():
            forward;            
            hello.appear;
            forward;
            world.appear;
            
        def bounce():
            delta = 0.01
            while True:
                for _ in range(10):
                    wait 0.1
                    hello.cy += delta
                    world.cy += delta
                delta = - delta   
                
        process unfold();
        process bounce();         
    """

    # canvas = presentation.flatten(canvas)

    presentation.present(canvas)
