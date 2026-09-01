# R20 repro_12: 多 kwonly 默认值（varnames 前部全为 kwonly）
def f(*args, x=1, y=2, z=3):
    return sum(args) + x + y + z


result = f(10, 20, x=5)
