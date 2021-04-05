#!/usr/bin/python3
# coding=utf8

from visuals.slide import Slide
from tasks.present import *

if __name__ == '__main__':

    camera = Window(1.6, 0.9, 1920, 1080, 2.5)

    slide = Slide(camera)

    text = Text("Hello World")

    square = Square(1, 1)

    image = Image("myimage.png")

    slide.add(text)
    slide.add(square)
    slide.add(image)

    display(slide, camera)
