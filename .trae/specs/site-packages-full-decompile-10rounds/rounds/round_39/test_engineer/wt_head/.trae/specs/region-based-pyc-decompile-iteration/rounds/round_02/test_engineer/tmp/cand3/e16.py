def f(o, a, b, env):
    o.x = a or env.a
    o.y = b or env.b
    return o
