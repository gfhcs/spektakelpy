# coding=utf8

from tkinter import *

from alpha import presentation

if __name__ == '__main__':

    p = presentation.Presentation(1920, 1080, fps=30)

    p.behavior = """
        def appear_soft(widget):
            for _ in range(params.framerate):
                wait(1 / params.framerate)
                widget.alpha += 0.1
                
        def bounce():
            delta = 0.01
            while True:
                for _ in range(10):
                    wait(0.1)
                    self.hello.cy += delta
                    self.world.cy += delta
                delta = - delta   

        process hello = Text("Hello")
        process world = Text("World")
        process _ = bounce()
        
        def present():
            self.hello.position = (0.5, 0.25)
            self.world.position = (0.5, 0.75)
            self.hello.alpha = 0
            self.world.alpha = 0
            
            forward
            appear_soft(hello)
            forward
            appear_soft(world)
    """

    p.present()
