# Source Generated with Decompyle++ (Python version)
# File: rec1_synth_compfilter_a.pyc (Python 3.11)

__doc__ = 'R2 合成变体 F6a（item 13 推导式折叠真值 orelse 过滤器族，非语料）。'
def p_listcomp(xs, f):
    return [x if f else 0 for x in xs if (x % 3 if f else True)]
def p_genexp(xs, f):
    return sum((1 for x in xs if (x if f else True)))
def p_dictcomp(ks, f):
    return {k: 1 for k in ks if (k if f else True)}
