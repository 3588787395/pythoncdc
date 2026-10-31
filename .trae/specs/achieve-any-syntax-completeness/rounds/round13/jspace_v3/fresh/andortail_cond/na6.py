def f(s):
    if s.startswith('x') and (s.endswith('y') or len(s) > 3):
        return True
    return False
