# Source Generated with Decompyle++ (Python version)
# File: r4v4r_b102_except.pyc (Python 3.11)

def one_star():
    try:
        pass
    except* ValueError:
        pass
def two_star():
    try:
        pass
    except* ValueError:
        pass
    except* TypeError:
        pass
def three_star():
    try:
        pass
    except* ValueError:
        pass
    except* TypeError:
        pass
    except* KeyError:
        pass
def normal_handlers():
    try:
        pass
    except ValueError:
        return None
    except TypeError:
        return None
def normal_finally():
    try:
        pass
    finally:
        pass
def star_else_finally():
    try:
        pass
    finally:
        pass
def nested_star():
    try:
        pass
    except* ValueError:
        pass
    except* TypeError:
        pass
    try:
        pass
    except Exception:
        return None
