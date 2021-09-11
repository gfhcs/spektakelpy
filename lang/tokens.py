from typing import NamedTuple


class TokenPosition(NamedTuple):
    offset: int
    line: int
    column: int

    def __str__(self):
        return "Line {}, column {}".format(self.line + 1, self.column + 1)

    def __repr__(self):
        return "Line {}, column {}".format(self.line + 1, self.column + 1)