def test():
    funcs = []
    for i in range(3):
        funcs.append(lambda x, i=i: x + i)
    return sum(f(10) for f in funcs)
