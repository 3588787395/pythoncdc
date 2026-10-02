# Source Generated with Decompyle++ (Python version)
# File: rv5_20_b20_var.pyc (Python 3.11)

__doc__ = 'Round5 复核变体探针：B20（跨 clause 过滤）修复的变体攻击。'
def c4_double_filters(xs, ys, zs, ws):
    """4 clause，每 clause 2 个过滤。"""
    return [w for x in xs if x and x > 1 for y in ys if y and y > 2 for z in zs if z and z > 3 for w in ws if w and w > 4]
def c_walrus_filters(xs, ys):
    """clause 过滤含 walrus。"""
    return [y + z for x in xs if (p := x) for y in ys if (z := y)]
def c_unpack_noninner_filter(xs, ys):
    """解包 target + 非最内层过滤组合。"""
    return [a + y for a, b in xs if a for y in ys if y]
def c3_walrus_unpack_mix(xs, ys, zs):
    """3 clause：解包 + 过滤 walrus + 尾过滤。"""
    return [a + z for a, b in xs if a for y in ys if (t := y) for z in zs if z]
