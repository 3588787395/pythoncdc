def f(s):
    if len(s) > 2 and s.startswith('a') and s.endswith('b') and (s.find('c') >= 0 or s.find('d') >= 0 or s.count('e') > 0):
        return True
    else:
        return False
