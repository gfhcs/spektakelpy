import io


def dedent(s):
    """
    Strips indendation white space from a program string. This is for Spek samples that we embed into Python code.
    :param s: The Spek string to dedent.
    :return: The dedented string.
    """
    d = 10 ** 32
    for line in s.splitlines():
        if line.strip() != "":
            d = min(d, len(line) - len(line.lstrip()))
    with io.StringIO() as out:
        for line in s.splitlines():
            if line.strip() == "":
                out.write(line)
            else:
                out.write(line[d:])
            out.write("\n")
        return out.getvalue()
