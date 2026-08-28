def f(o, a, b, c, env):
    o.x = a or env.a
    o.y = b or env.b
    o.z = c
    return o
