# rv3_03: B85/B86 回归攻击——函数域链式赋值 + 多上下文 with（守卫域外推：函数域原本正确，修复后必须仍正确）
import os as _os


def chain_assign():
    a = b = c = {'k': 1}
    d = e = [1, 2, 3]
    f = g = h = a
    return a, b, c, d, e, f, g, h


def multi_with(p):
    r1 = r2 = None
    with open(p, 'w') as fa, open(p + '.bak', 'w') as fb:
        fa.write('x')
        fb.write('y')
        r1 = fa
        r2 = fb
    with _os.popen('echo hi') as fc, _os.popen('echo yo') as fd:
        r1 = fc.readline()
        r2 = fd.readline()
    return r1, r2
