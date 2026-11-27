def wf(open, ctx, Ctx, Ctx2):
    with open('x') as f: pass
    with ctx() as (a, b): pass
    with Ctx() as c, Ctx2() as d: pass
    with ctx() as (p, q), open('y') as fy: pass
