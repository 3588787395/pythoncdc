def test():
    data = ['hello', 'world', 'python']
    return [s.upper() for s in data if len(s) > 3]
