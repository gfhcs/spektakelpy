import os.path

root = os.path.dirname(os.path.realpath(__file__))

paths = []

for fn in os.listdir(root):

    fp = os.path.join(root, fn)
    _, ext = os.path.splitext(fp)

    if os.path.isfile(fp) and ext == ".spek":
        paths.append(fp)

paths = sorted(paths)
del root
