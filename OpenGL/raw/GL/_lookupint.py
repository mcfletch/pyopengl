# mypy: ignore-errors
# The names in this module arrive from the declaration tables at import
# time, so a checker reading this file sees calls to things it cannot
# find.  The typed surface is the .pyi stub beside the package.
"""Integer values looked up via glGetIntegerv( constant )"""

import ctypes

_get = None
_get_float = None


class LookupInt(object):
    def __init__(self, lookup, format=ctypes.c_int, calculation=None):
        self.lookup = lookup
        self.format = format
        self.calculation = calculation

    def __int__(self):
        global _get
        if _get is None:
            from OpenGL.GL import glGetIntegerv

            _get = glGetIntegerv
        output = self.format()
        _get(self.lookup, output)
        if self.calculation:
            return self.calculation(output.value)
        return output.value

    __long__ = __int__

    def __eq__(self, other):
        return int(self) == other

    def __cmp__(self, other):
        test = int(self)
        return (test > other) - (test < other)

    def __lt__(self, other):
        return int(self) < other

    def __gt__(self, other):
        return int(self) > other

    def __eq__(self, other):
        return int(self) == other

    def __str__(self):
        return str(int(self))

    __repr__ = __str__
