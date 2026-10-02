# Source Generated with Decompyle++ (Python version)
# File: r4_05_match_class.pyc (Python 3.11)

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
class Color:
    def __init__(self, r, g, b):
        self.r = r
        self.g = g
        self.b = b
def match_class_kwargs(p):
    """Attack 1: class pattern with keyword patterns."""
    match p:
        case Point(x=0, y=0):
            return 'origin'
        case Point(x=0, y=y):
            return ('y', y)
        case Point(x=0, y=x):
            return ('x', x)
        case Point(x=x, y=y):
            return ('xy', x, y)
        case _:
            return 'notpoint'
def match_class_positional(p):
    """Attack 2: class pattern with positional patterns (needs __match_args__)."""
    match p:
        case Color(0, 0, 0):
            return 'black'
        case Color(255, 255, 255):
            return 'white'
        case Color(r, g, b):
            return (r, g, b)
        case _:
            return 'notcolor'
def match_class_mixed(p):
    """Attack 3: positional + keyword mixed class pattern."""
    match p:
        case Point(0, y=y):
            return ('on-y-axis', y)
        case Point(x=x, y=y) if x == y:
            return ('diagonal', x)
        case Point(x=x):
            return ('x-only', x)
        case _:
            return 'other'
def match_class_nested_value(p):
    """Attack 4: class pattern with nested literal/sequence patterns."""
    match p:
        case Point(x=0, y=0):
            return 0
        case Point(x=x, y=y):
            return 1
        case Point(x=x, y=y):
            return abs(x) + abs(y)
        case _:
            return -1
