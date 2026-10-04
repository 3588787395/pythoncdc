# Source Generated with Decompyle++ (Python version)
# File: rv10_31_nonlocal_variant.pyc (Python 3.11)

__doc__ = 'rv10_31: B72 守卫边界外推 — nonlocal 只读/del/双链/增量赋值/循环宿主'
def v_nonlocal_readonly(flag):
    """闭包只读自由变量（LOAD_DEREF 无 STORE_DEREF）——守卫不应声明 nonlocal"""
    anchor = flag * 3
    def reader():
        return anchor + 1
    return reader
def v_nonlocal_del(n):
    """nonlocal 声明 + del（DELETE_DEREF）"""
    box = n
    def drop():
        nonlocal box
        del box
        return 0
    drop()
    return n
def v_dual_chain(seed):
    """两条并行闭包链各自 nonlocal 写"""
    left = seed
    right = seed * 2
    def lift():
        nonlocal left
        left += 1
        def deep():
            nonlocal left, right
            left *= 2
            right -= 1
            return left + right
        return deep()
    def shift():
        nonlocal right
        right <<= 1
        return right
    return (lift(), shift())
def v_nonlocal_augassign(rows):
    """nonlocal + 增量赋值（STORE_DEREF 前有 LOAD_DEREF + BINARY_OP）"""
    total = 0
    def absorb(xs):
        nonlocal total
        for x in xs:
            if x > 0:
                total += x
                continue
            elif x < -5:
                total -= 1
        return total
    return absorb(rows)
def v_nonlocal_in_loop(limit):
    """循环体内定义闭包并写自由变量"""
    best = limit
    for k in range(3):
        def probe(v):
            nonlocal best
            if v > best:
                best = v
            return best
        probe(k * 7)
    return best
