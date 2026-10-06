#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round 7（已封闭守卫族守卫判据面重攻击）探针程序化生成器。只写 test_repros/round7/r7v7_*.py 与 n7v7_*.py。

口径注记（前缀冲突处置）：
- test_repros/round7/ 已存在旧规范 round7 的已跟踪文件（r7_01..r7_14 / n7_01..n7_02 / rv7_01..rv7_04 共 61 文件），
  故本轮**不**复用 r7_*/n7_*/rv7_* 前缀（会覆盖 tracked 文件），改用轮次专属 r7v7_（攻击）/ n7v7_（负对照）。
- 宿主条件一律非常量，禁用 `if 1:` / `while 1:` + break（CPython 常量折叠伪差）。
- 攻击对象 = spec III.5 三大已封闭守卫族（B2 If×continue / B3 Loop 共享尾 / B4 孤儿子）× 三方向：
  (a) 守卫适用形态变体（深层 ≥3、类体/循环体/try 体互为宿主）
  (b) 守卫边界外形态（应走通用算法，验证守卫不误吞也不漏接）
  (c) 守卫互斥/交互组合（两守卫同现不打架）
- 每探针含 shallow（深度 1）与 deep（深度 ≥3）同形态孪生函数 → 实测判据 C2「深层与浅层产物结构一致」。
- 守卫落地锚点（spec III.5，round6 注释批次后行号有漂移，以 grep 实际代码为准）：
  B2: region_ast_generator.py `_block_is_continue_target`(:12954) / `_block_is_pure_continue`(:13029) /
      条件取反×内层 if-continue 重组(:21704-21737) / merge==back_edge 无条件 continue 兄弟(:21845+) /
      `_is_with_exit_back_edge`(:13056) / B66 continue 链头(:3414)
  B3: region_ast_generator.py `_is_loop_tail_convergence_block`(:12963 显式 Continue 冗余抑制·前驱≥2 判据)；
      region_analyzer.py W14-C 共享尾归属(:21659-21680) / B109 真 loop-else(:4864-4911) /
      `_find_loop_else`(:5722) / `_loop_else_nop_marker`(:5630) / `_clamp_loop_else_to_enclosing_try`(:5585)
  B4: region_ast_generator.py 孤儿块释放·顶级祖先检查(:1717-1800)；region_analyzer.py
      R09 空 try 体 finally 孤儿帧(:1460) / R21 handler 返回后继认领(:9017-9019)
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))

PROBES = {}

# ═════════════════════════════════════════════════════════════════════════
# B2 If×continue 守卫族
# ═════════════════════════════════════════════════════════════════════════

# (a) 守卫适用形态变体：for→if→if→if: continue 深度 3
PROBES['r7v7_b2a01'] = r'''
def b2a01_shallow(xs, flag):
    acc = 0
    for x in xs:
        if x > 3:
            continue
        acc += x
    return acc


def b2a01_deep(xs, flag):
    acc = 0
    for x in xs:
        if flag:
            if x > 1:
                if x > 2:
                    if x > 3:
                        continue
                    acc -= 1
                acc += 2
            acc += 3
        acc += x
    return acc
'''

# (a) try 体宿主：while→try→for→if: continue
PROBES['r7v7_b2a02'] = r'''
def b2a02_shallow(items, limit):
    out = []
    for it in items:
        if it > limit:
            continue
        out.append(it)
    return out


def b2a02_deep(items, limit):
    out = []
    while limit > 0:
        try:
            for it in items:
                if it > 0:
                    if it > limit:
                        continue
                    out.append(it)
        except ValueError:
            limit = 0
        limit -= 1
    return out
'''

# (a) 类体宿主：方法内 for→if→if: continue + else 臂
PROBES['r7v7_b2a03'] = r'''
class B2A03:
    def b2a03_shallow(self, xs, flag):
        acc = 0
        for x in xs:
            if x < 0 and flag:
                continue
            acc += x
        return acc

    def b2a03_deep(self, xs, flag):
        acc = 0
        for x in xs:
            if flag:
                if x != 0:
                    if x < 0:
                        continue
                    acc += x
                else:
                    acc -= 1
        return acc
'''

# (a) elif 链分支 = continue，深度 3
PROBES['r7v7_b2a04'] = r'''
def b2a04_shallow(ks, flag):
    total = 0
    for k in ks:
        if k == 'a':
            total += 1
        elif k == 'b':
            continue
        elif k == 'c':
            total += 3
        total += 100
    return total


def b2a04_deep(ks, flag, mode):
    total = 0
    for k in ks:
        if mode:
            if flag:
                if k == 'a':
                    total += 1
                elif k == 'b':
                    continue
                elif k == 'c':
                    total += 3
            total += 100
        total += 1
    return total
'''

# (a) 非纯 continue（if 体尾带语句再 continue），深度 3
PROBES['r7v7_b2a05'] = r'''
def b2a05_shallow(xs, flag):
    acc = 0
    for x in xs:
        if x > 5:
            acc -= 1
            continue
        acc += x
    return acc


def b2a05_deep(xs, flag):
    acc = 0
    while xs:
        if flag:
            if acc > 0:
                if len(xs) > 5:
                    acc -= 1
                    continue
                acc += 1
        xs = xs[1:]
    return acc
'''

# (a) 嵌套双循环各自 continue（内层 continue 回内层回边），深度 3
PROBES['r7v7_b2a06'] = r'''
def b2a06_shallow(xs, ys, flag):
    acc = 0
    for x in xs:
        if x == 0:
            continue
        for y in ys:
            if y == 0:
                continue
            acc += x * y
    return acc


def b2a06_deep(xs, ys, flag):
    acc = 0
    for x in xs:
        if flag:
            if x == 0:
                continue
            for y in ys:
                if flag and y == 0:
                    continue
                if y < 0:
                    if y == -1:
                        continue
                    acc += x
                acc += x * y
    return acc
'''

# (b) 守卫边界外：if c: break（Break 语义，不得误吞为 Continue）
PROBES['r7v7_b2b01'] = r'''
def b2b01_shallow(xs, flag):
    acc = 0
    for x in xs:
        if x > 9:
            break
        acc += x
    return acc


def b2b01_deep(xs, flag):
    acc = 0
    for x in xs:
        if flag:
            if acc > 0:
                if x > 9:
                    break
                acc += 1
        acc += x
    return acc
'''

# (b) 守卫边界外：if c: return X（Return 语义）
PROBES['r7v7_b2b02'] = r'''
def b2b02_shallow(xs, flag):
    for x in xs:
        if x is None:
            return False
    return True


def b2b02_deep(xs, flag):
    n = 0
    for x in xs:
        if flag:
            if x > 0:
                if x is None:
                    return False
                n += 1
    return n
'''

# (b) 守卫边界外：条件取反 + 内层 if-continue **无 else**（重组守卫要求 orelse，缺 else 应走通用算法）
PROBES['r7v7_b2b03'] = r'''
def b2b03_shallow(ks, flag):
    n = 0
    for k in ks:
        if k != 'x':
            if k == 'y':
                continue
            n += 1
    return n


def b2b03_deep(ks, flag):
    n = 0
    for k in ks:
        if flag:
            if k != 'x':
                if k == 'y':
                    continue
                n += 1
    return n
'''

# (b) 守卫边界外：else 分支 continue（then 语句 / else continue）
PROBES['r7v7_b2b04'] = r'''
def b2b04_shallow(xs, flag):
    acc = 0
    for x in xs:
        if x > 0:
            acc += x
        else:
            continue
        acc += 1
    return acc


def b2b04_deep(xs, flag):
    acc = 0
    for x in xs:
        if flag:
            if x > 0:
                if x > 100:
                    acc -= x
                else:
                    acc += x
            else:
                continue
        else:
            acc += 2
        acc += 1
    return acc
'''

# (c) 守卫交互组合：If×continue 与 Loop 共享尾同现（continue 守卫 + 回边汇合抑制守卫）
PROBES['r7v7_b2c01'] = r'''
def b2c01_shallow(xs, flag):
    acc = 0
    for x in xs:
        if x % 2 == 0:
            if flag:
                continue
        acc += x
        acc += 1
    return acc


def b2c01_deep(xs, flag):
    acc = 0
    for x in xs:
        if flag:
            if x > 0:
                if x % 2 == 0:
                    if flag:
                        continue
                acc += x
        acc += 1
        acc += acc > 1000
    return acc
'''

# (c) 守卫交互组合：then 与 else 双 continue（两分支均指向回边）
PROBES['r7v7_b2c02'] = r'''
def b2c02_shallow(xs, k):
    n = 0
    for x in xs:
        if x == k:
            continue
        else:
            continue
    return n


def b2c02_deep(xs, k, flag):
    n = 0
    for x in xs:
        if flag:
            if x > 0:
                if x == k:
                    continue
                else:
                    continue
            n += 1
    return n
'''

# (c) 守卫交互组合：continue 与 break 同 if/else（Continue 节点 + Break 节点同区域）
PROBES['r7v7_b2c03'] = r'''
def b2c03_shallow(xs, k):
    acc = 0
    for x in xs:
        if x == k:
            continue
        else:
            break
    return acc


def b2c03_deep(xs, k, flag):
    acc = 0
    while xs:
        if flag:
            if acc >= 0:
                if xs[0] == k:
                    continue
                else:
                    break
        acc += 1
        xs = xs[1:]
    return acc
'''

# ═════════════════════════════════════════════════════════════════════════
# B3 Loop 共享尾守卫族
# ═════════════════════════════════════════════════════════════════════════

# (a) for: if c: S 共享尾（f2 形态·回边块前驱 ≥2）深度 3
PROBES['r7v7_b3a01'] = r'''
def b3a01_shallow(xs, flag):
    acc = 0
    for x in xs:
        if x > 0:
            acc += x
        acc += 1
    return acc


def b3a01_deep(xs, flag):
    acc = 0
    for x in xs:
        if flag:
            if x > 0:
                if x > 10:
                    acc += 100
                else:
                    acc += x
            acc += 1
        acc += 2
    return acc
'''

# (a) while 宿主共享尾，深度 3
PROBES['r7v7_b3a02'] = r'''
def b3a02_shallow(n, flag):
    s = 0
    while n > 0:
        if n % 2 == 0:
            s += n
        n -= 1
    return s


def b3a02_deep(n, flag):
    s = 0
    while n > 0:
        if flag:
            if n > 5:
                if n % 2 == 0:
                    s += n
                else:
                    s += 1
            n -= 1
        else:
            s += 2
            n -= 2
    return s
'''

# (a) try 体宿主共享尾，深度 3
PROBES['r7v7_b3a03'] = r'''
def b3a03_shallow(xs, flag):
    acc = 0
    try:
        for x in xs:
            if x > 0:
                acc += x
            acc += 1
    except TypeError:
        acc = -1
    return acc


def b3a03_deep(xs, flag):
    acc = 0
    try:
        if flag:
            for x in xs:
                if x > 0:
                    if x > 100:
                        acc += 10
                    else:
                        acc += x
                acc += 1
    except TypeError:
        acc = -1
    return acc
'''

# (a) 类方法宿主共享尾
PROBES['r7v7_b3a04'] = r'''
class B3A04:
    def b3a04_shallow(self, xs, flag):
        total = 0
        for x in xs:
            if x:
                total += x
            total += 1
        return total

    def b3a04_deep(self, xs, flag):
        total = 0
        for x in xs:
            if flag:
                if x:
                    if x > 5:
                        total += 5
                    total += x
            total += 1
        return total
'''

# (a) 嵌套双循环各自共享尾，深度 3
PROBES['r7v7_b3a05'] = r'''
def b3a05_shallow(xs, ys, flag):
    acc = 0
    for x in xs:
        if x > 0:
            for y in ys:
                if y > 0:
                    acc += x * y
                acc += y
        acc += x
    return acc


def b3a05_deep(xs, ys, flag):
    acc = 0
    for x in xs:
        if flag:
            if x != 0:
                for y in ys:
                    if flag:
                        if y != 0:
                            if y > 0:
                                acc += x * y
                            acc += y
                acc += x
        acc += 1
    return acc
'''

# (a) 共享尾含调用副作用（必须恰好发射一次），深度 3
PROBES['r7v7_b3a06'] = r'''
def b3a06_shallow(xs, flag, sink):
    for x in xs:
        if x > 0:
            sink.append(x)
        sink.append(0)
    return len(sink)


def b3a06_deep(xs, flag, sink):
    for x in xs:
        if flag:
            if x > 0:
                if x % 3 == 0:
                    sink.append(x)
                else:
                    sink.append(-x)
            sink.append(0)
    return len(sink)
'''

# (b) 守卫边界外：显式 continue（f1 形态·continue 块单前驱，不得被汇合抑制守卫误吞）
PROBES['r7v7_b3b01'] = r'''
def b3b01_shallow(xs, flag):
    acc = 0
    for x in xs:
        if x < 0:
            continue
        acc += x
    return acc


def b3b01_deep(xs, flag):
    acc = 0
    for x in xs:
        if flag:
            if acc >= 0:
                if x < 0:
                    continue
                acc += x
        else:
            acc -= 1
    return acc
'''

# (b) 守卫边界外：真 loop-else（break 证据）——for + break + else，深度 3
PROBES['r7v7_b3b02'] = r'''
def b3b02_shallow(xs, k):
    for x in xs:
        if x == k:
            break
    else:
        return -1
    return 1


def b3b02_deep(xs, k, flag):
    res = 0
    if flag:
        for x in xs:
            if x > 0:
                if x == k:
                    break
        else:
            res = -1
        res += 1
    return res
'''

# (b) 守卫边界外：真 while-else，深度 3
PROBES['r7v7_b3b03'] = r'''
def b3b03_shallow(n, k):
    while n > 0:
        if n == k:
            break
        n -= 1
    else:
        return -1
    return 1


def b3b03_deep(n, k, flag):
    res = 0
    while n > 0:
        if flag:
            if n > 5:
                if n == k:
                    break
        n -= 1
    else:
        res = -1
    return res
'''

# (c) 守卫交互组合：共享尾 + If×continue 同循环同现
PROBES['r7v7_b3c01'] = r'''
def b3c01_shallow(xs, flag):
    acc = 0
    for x in xs:
        if x == -1:
            continue
        if x > 0:
            acc += x
        acc += 1
    return acc


def b3c01_deep(xs, flag):
    acc = 0
    for x in xs:
        if flag:
            if x == -1:
                continue
            if x > 0:
                if x > 100:
                    acc += 100
                else:
                    acc += x
            acc += 1
        else:
            acc += 2
    return acc
'''

# (c) 守卫交互组合：loop-else + 共享尾 + continue 三守卫同现
PROBES['r7v7_b3c02'] = r'''
def b3c02_shallow(xs, k):
    acc = 0
    for x in xs:
        if x == k:
            continue
        acc += x
    else:
        acc += 1000
    return acc


def b3c02_deep(xs, k, flag):
    acc = 0
    for x in xs:
        if flag:
            if x > 0:
                if x == k:
                    continue
            acc += x
        else:
            acc -= 1
    else:
        acc += 1000
    return acc
'''

# (c) 守卫交互组合：跨层共享尾（内层 if 尾与外层 if 尾逐层汇合），深度 4
PROBES['r7v7_b3c03'] = r'''
def b3c03_shallow(xs, flag):
    acc = 0
    for x in xs:
        if x > 0:
            if flag:
                acc += x
            acc += 1
        acc += 2
    return acc


def b3c03_deep(xs, flag):
    acc = 0
    for x in xs:
        if x != 0:
            if x > 0:
                if flag:
                    if x > 10:
                        acc += 10
                    else:
                        acc += x
                acc += 1
            acc += 2
        acc += 3
    return acc
'''

# ═════════════════════════════════════════════════════════════════════════
# B4 孤儿子守卫族
# ═════════════════════════════════════════════════════════════════════════

# (a) 嵌套 if/else 汇合块（孤儿块高发）深度 4
PROBES['r7v7_b4a01'] = r'''
def b4a01_shallow(xs, flag):
    acc = 0
    for x in xs:
        if x > 0:
            if x > 5:
                acc += 5
            else:
                acc += x
        acc += 1
    return acc


def b4a01_deep(xs, flag):
    acc = 0
    for x in xs:
        if x != 0:
            if x > 0:
                if x > 5:
                    if x > 50:
                        acc += 50
                    else:
                        acc += 5
                else:
                    acc += x
            acc += 1
        acc += 2
    return acc
'''

# (a) try 内 try 内循环 + finally（孤儿 finally 帧），深度 3
PROBES['r7v7_b4a02'] = r'''
def b4a02_shallow(xs, flag):
    acc = 0
    try:
        for x in xs:
            try:
                acc += x
            finally:
                acc += 1
    finally:
        acc += 2
    return acc


def b4a02_deep(xs, flag):
    acc = 0
    if flag:
        try:
            for x in xs:
                if x > 0:
                    try:
                        if x > 10:
                            acc += 10
                        else:
                            acc += x
                    finally:
                        acc += 1
                else:
                    acc -= 1
        finally:
            acc += 2
    return acc
'''

# (a) 空 try 体 + finally（R09 孤儿 finally 帧）宿主=循环体+if，深度 3
PROBES['r7v7_b4a03'] = r'''
def b4a03_shallow(flag):
    if flag:
        try:
            pass
        finally:
            flag = not flag
    return flag


def b4a03_deep(flag, n):
    while n > 0:
        if flag:
            try:
                pass
            finally:
                flag = not flag
        n -= 1
    return flag
'''

# (a) 类方法宿主：try/finally + 嵌套 if 汇合
PROBES['r7v7_b4a04'] = r'''
class B4A04:
    def b4a04_shallow(self, xs, flag):
        acc = 0
        try:
            for x in xs:
                if x > 0:
                    acc += x
        finally:
            acc += 1
        return acc

    def b4a04_deep(self, xs, flag):
        acc = 0
        try:
            if flag:
                for x in xs:
                    if x > 0:
                        if x > 10:
                            acc += 10
                        else:
                            acc += x
        finally:
            acc += 1
        return acc
'''

# (a) with 体宿主：with→if→for→if 汇合块，深度 3
PROBES['r7v7_b4a05'] = r'''
def b4a05_shallow(path, xs, flag):
    acc = 0
    with open(path) as f:
        for x in xs:
            if x > 0:
                acc += x
            acc += 1
    return acc


def b4a05_deep(path, xs, flag):
    acc = 0
    with open(path) as f:
        if flag:
            for x in xs:
                if x > 0:
                    if x > 10:
                        acc += 10
                    else:
                        acc += x
                acc += 1
    return acc
'''

# (a) try 体仅表达式 + finally（非抛出体孤儿帧），深度 3
PROBES['r7v7_b4a06'] = r'''
def b4a06_shallow(a, b):
    try:
        a + b
    finally:
        a = b
    return a


def b4a06_deep(a, b, flag):
    if flag:
        if a > 0:
            try:
                a + b
            finally:
                a = b
    return a
'''

# (b) 守卫边界外：合法嵌套子区域块（有顶级祖先，不得释放 → 不得出现幻影语句），深度 4
PROBES['r7v7_b4b01'] = r'''
def b4b01_shallow(xs, flag):
    acc = 0
    for x in xs:
        if x > 0:
            acc += 1
        else:
            acc -= 1
    return acc


def b4b01_deep(xs, flag):
    acc = 0
    if flag:
        for x in xs:
            if x > 0:
                if x > 10:
                    if x > 100:
                        acc += 3
                    else:
                        acc += 2
                else:
                    acc += 1
            else:
                if x < -10:
                    acc -= 3
                else:
                    acc -= 1
    return acc
'''

# (b) 守卫边界外：try/except 后 return（R21 handler 返回后继认领形态），深度 3
PROBES['r7v7_b4b02'] = r'''
def b4b02_shallow(xs, k):
    try:
        i = xs.index(k)
    except ValueError:
        return -1
    return i


def b4b02_deep(xs, k, flag):
    if flag:
        try:
            if k > 0:
                i = xs.index(k)
            else:
                i = -2
        except ValueError:
            return -1
        return i
    return -3
'''

# (b) 守卫边界外：try/except/else 三段（else 段汇合块归属），深度 3
PROBES['r7v7_b4b03'] = r'''
def b4b03_shallow(xs, k):
    try:
        v = xs[0]
    except IndexError:
        v = -1
    else:
        v = v + k
    return v


def b4b03_deep(xs, k, flag):
    if flag:
        if k > 0:
            try:
                v = xs[0]
            except IndexError:
                v = -1
            else:
                v = v + k
    return v
'''

# (c) 守卫交互组合：孤儿汇合块 + Loop 共享尾（B4×B3）
PROBES['r7v7_b4c01'] = r'''
def b4c01_shallow(xs, flag):
    acc = 0
    for x in xs:
        if x > 0:
            if flag:
                acc += x
            else:
                acc -= x
        acc += 1
    return acc


def b4c01_deep(xs, flag):
    acc = 0
    for x in xs:
        if x != 0:
            if x > 0:
                if flag:
                    if x > 100:
                        acc += 100
                    else:
                        acc += x
                else:
                    acc -= x
        acc += 1
    return acc
'''

# (c) 守卫交互组合：孤儿 finally 帧 + If×continue（B4×B2）
PROBES['r7v7_b4c02'] = r'''
def b4c02_shallow(xs, k):
    acc = 0
    for x in xs:
        try:
            if x == k:
                continue
            acc += x
        finally:
            acc += 1
    return acc


def b4c02_deep(xs, k, flag):
    acc = 0
    while xs:
        if flag:
            try:
                if xs[0] == k:
                    continue
                if xs[0] > 0:
                    acc += xs[0]
            finally:
                acc += 1
        xs = xs[1:]
    return acc
'''

# (c) 守卫交互组合：孤儿汇合块 + loop-else（B4×B3 loop-else 守卫）
PROBES['r7v7_b4c03'] = r'''
def b4c03_shallow(xs, k):
    acc = 0
    for x in xs:
        if x > 0:
            if x == k:
                acc = -1
                break
            acc += x
        else:
            acc -= 1
    else:
        acc += 100
    return acc


def b4c03_deep(xs, k, flag):
    acc = 0
    if flag:
        for x in xs:
            if x > 0:
                if x == k:
                    acc = -1
                    break
                if x > 10:
                    acc += 10
                else:
                    acc += x
            else:
                acc -= 1
        else:
            acc += 100
    return acc
'''

# ═════════════════════════════════════════════════════════════════════════
# 负对照（浅层/朴素形态，必须保持 MATCH）
# ═════════════════════════════════════════════════════════════════════════

PROBES['n7v7_b2n01'] = r'''
def n2a(xs, flag):
    acc = 0
    for x in xs:
        if x > 0:
            continue
        acc += x
    return acc


def n2b(n, flag):
    s = 0
    while n > 0:
        n -= 1
        if n % 2:
            continue
        s += n
    return s
'''

PROBES['n7v7_b2n02'] = r'''
def n2c(xs, flag):
    acc = 0
    for x in xs:
        if x < 0:
            acc -= 1
            continue
        acc += x
    else:
        acc += 1000
    return acc


def n2d(xs, k):
    n = 0
    for x in xs:
        if x == k:
            continue
        else:
            n += 1
    return n
'''

PROBES['n7v7_b3n01'] = r'''
def n3a(xs, flag):
    acc = 0
    for x in xs:
        if x > 0:
            acc += x
        acc += 1
    return acc


def n3b(n, flag):
    s = 0
    while n > 0:
        if n > 5:
            if n % 2 == 0:
                s += n
            else:
                s += 1
        n -= 1
    return s
'''

PROBES['n7v7_b3n02'] = r'''
def n3c(xs, k):
    for x in xs:
        if x == k:
            break
    else:
        return -1
    return 1


def n3d(n, k):
    while n > 0:
        if n == k:
            break
        n -= 1
    else:
        return -1
    return 1
'''

PROBES['n7v7_b4n01'] = r'''
def n4a(x, flag):
    acc = 0
    try:
        if x > 0:
            acc += 1
        else:
            acc -= 1
    finally:
        acc += 10
    return acc


def n4b(xs, flag):
    acc = 0
    for x in xs:
        if x:
            acc += 1
    else:
        acc += 100
    return acc
'''

PROBES['n7v7_b4n02'] = r'''
def n4c(xs, k):
    try:
        i = xs.index(k)
    except ValueError:
        return -1
    return i


def n4d(xs, flag):
    total = 0
    for x in xs:
        total += x
    return total
'''


def main():
    written = 0
    for stem, body in sorted(PROBES.items()):
        path = os.path.join(HERE, stem + '.py')
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(body.lstrip('\n'))
        written += 1
    print('wrote %d probe sources -> %s' % (written, HERE))


if __name__ == '__main__':
    main()
