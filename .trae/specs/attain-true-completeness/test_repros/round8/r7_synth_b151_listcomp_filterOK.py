# Source Generated with Decompyle++ (Python version)
# File: r7_synth_b151_listcomp_filter.pyc (Python 3.11)

def s_b151_listcomp_filter(xs, lim, flag):
    return [x for x in xs if 0 < x < lim and (flag or x % 2)]
def s_b151_listcomp_filter2(xs, flag):
    return [x * 2 for x in xs if x and flag]
def s_b151_listcomp_filter3(xs, lim, flag):
    return [x for x in xs if flag or x % 2 and x < lim]
