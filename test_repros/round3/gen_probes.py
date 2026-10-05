#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round 3 探针生成器（对抗完备形态 v2 · Round 3 · 表B 表达式形态对抗）。

程序化生成 G1-G10 攻击探针（e* 前缀）与 MATCH 负对照（ne* 前缀）。
探针协议（round2 教训全承接）：
  - 禁用 if 1:/while 1: + break 折叠宿主形（CPython 优化留跳转目标 NOP 残段
    → 零长异常区间 → 探针退化伪差必差）；一律非常量条件
  - 表达式操作数用参数/变量，防 CPython 常量折叠
  - 每文件多函数 = 多单元；每大组 >=10 个深层单元（深度 >=3）+ >=2 负对照单元

组主题（spec III.3 表B 全名单 x 深嵌套宿主）：
  G1  BoolOp/B1 台账复核 + B98 分组 boolop 保真专攻（最高优先）
  G2  IfExp 三元（链式/分组交叉/实参/返回值/推导式条件/默认参数）
  G3  Compare 链 + 操作符叶子全遍历（Add..NotIn + UnaryOp）
  G4  BinOp/UnaryOp/Starred/Slice/Subscript/容器字面量
  G5  Lambda（闭包/默认参/返回值/排序 key/装饰器工厂/三元 boolop 体）
  G6  推导式族（ListComp/SetComp/DictComp/GenExp/嵌套/多 for+条件/海象/await）
  G7  Call/keyword_args/star_args（kwargs 混位置/*args/**kwargs/调用链/方法链）
  G8  JoinedStr/FormattedValue + fstring_conversion（!r/!s/!a/嵌套 spec/嵌 f）
  G9  Await/Yield/YieldFrom 表达式位（B95/B96 已封闭面回归）
  G10 NamedExpr 海象（while/if 条件/推导式条件/lambda 默认参/链/RHS 三元 boolop）
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# ────────────────────────────────────────────────────────────────────
# G1 ★BoolOp/B1 台账复核 + B98 专攻
# ────────────────────────────────────────────────────────────────────

E01 = '''\
# e01: B98 爆炸半径测绘——分组 boolop 保真（内层 or + 外层 and / 内层 and + 外层 or）
# 宿主：函数体深嵌套（for→if→while / for→if）深度 >=3；与三元/比较/海象/条件位交叉

def f_or_in_and_deep(a, b, c):
    acc = []
    for i in range(3):
        if i % 2 == 0:
            while len(acc) < 4:
                r = (a or b) and c
                acc.append(r)
                break
    return acc


def f_and_in_or_deep(a, b, c):
    acc = []
    for i in range(3):
        if i:
            while len(acc) < 4:
                r = a or (b and c)
                acc.append(r)
                break
    return acc


def f_or_in_and_pair_deep(a, b, c, d):
    acc = []
    for i in range(3):
        if i:
            while len(acc) < 4:
                r = (a or b) and (c or d)
                acc.append(r)
                break
    return acc


def f_b98_ternary_cross(a, b, c, d):
    for i in range(3):
        if i:
            while i < 4:
                return ((a or b) and c) if d else 0
    return 1


def f_b98_compare_cross(a, b, c):
    for i in range(3):
        if i:
            while i:
                return ((a or b) and c) > 2
    return False


def f_b98_walrus_cross(a, b, c):
    for i in range(3):
        if i:
            if (w := (a or b) and c):
                return w
    return 0


def f_b98_if_cond_pos(a, b, c):
    for i in range(3):
        if (a or b) and c:
            if i:
                return i
    return 0


def f_b98_while_cond_pos(a, b, c):
    n = 0
    while (a or b) and c:
        if n > 2:
            break
        n += 1
    return n


def f_b98_return_pos(a, b, c):
    for i in range(3):
        if i == 1:
            return (a or b) and c
    return 0


def f_b98_call_arg_pos(a, b, c):
    def sink(x):
        return x + 1
    for i in range(3):
        if i:
            return sink((a or b) and c)
    return 0


def f_b98_or_tail_and_group(a, b, c, d):
    for i in range(3):
        if i:
            if (a and b) or c or d:
                return i
    return 0


def f_b98_not_wrapped(a, b, c):
    for i in range(3):
        if i:
            return 1 if not ((a or b) and c) else 2
    return 0


def f_b98_and_tail_or_group(a, b, c, d):
    acc = []
    for i in range(3):
        if i:
            while len(acc) < 3:
                r = (a or b) and (c or d) and a
                acc.append(r)
                break
    return acc
'''

E02 = '''\
# e02: B98 宿主矩阵——模块根/类体/handler 臂/推导式条件位/嵌套函数/match 臂/with 体
_P, _Q, _R, _S = 1, 2, 3, 4

M1 = (_P or _Q) and _R
M2 = _P or (_Q and _R)


class CB98:
    C1 = (_P or _Q) and _R
    C2 = _P or (_Q and _R)

    def m_handler(self, a, b, c):
        try:
            for i in range(3):
                if i:
                    return (a or b) and c
        except ValueError:
            return ((a or b) and c) if a else -1
        return 0

    def m_class_body_host(self, a, b, c):
        for i in range(2):
            if i:
                return a or (b and c)
        return 0


def f_comp_cond_host(a, b, c, xs):
    for i in range(2):
        if i:
            return [x for x in xs if (a or b) and c]
    return []


def f_genexp_cond_host(a, b, c, xs):
    for i in range(2):
        if i:
            return sum(1 for x in xs if (a or b) and c)
    return 0


def f_dictcomp_value_host(a, b, c, xs):
    for i in range(2):
        if i:
            return {x: ((a or b) and c) for x in xs if x}
    return {}


def f_nested_func_host(a, b, c):
    def inner():
        for i in range(3):
            if i:
                return (a or b) and c
        return 0
    for j in range(2):
        if j:
            return inner()
    return 0


def f_match_arm_host(a, b, c, cmd):
    for i in range(2):
        if i:
            match cmd:
                case 1:
                    return (a or b) and c
                case _:
                    return a or (b and c)
    return 0


def f_with_body_host(a, b, c):
    class CM:
        def __enter__(self):
            return self

        def __exit__(self, *e):
            return False
    with CM() as cm:
        for i in range(2):
            if i:
                return (a or b) and c
    return 0


def f_try_body_host(a, b, c):
    try:
        for i in range(2):
            if i:
                return (a or b) and c
    except KeyError:
        return -1
    return 0
'''

E03 = '''\
# e03: B1b 五臂封闭（[B1b fix]/[B1b fix-r2] + _sb_has_body）外推 + 收缩双向变体攻击
def f_b1b_stmt_or_tail(a, b, c):
    for i in range(3):
        if i:
            if a and b or c:
                return i
    return 0


def f_b1b_shrink_or3(a, b, c):
    for i in range(3):
        if i:
            if a or b or c:
                return i
    return 0


def f_b1b_shrink_and3(a, b, c):
    for i in range(3):
        if i:
            if a and b and c:
                return i
    return 0


def f_b1b_and_or_and(a, b, c, d):
    for i in range(3):
        if i:
            if a and b or c and d:
                return i
    return 0


def f_b1b_deep_right(a, b, c, d):
    for i in range(3):
        if i:
            if a or (b and (c or d)):
                return i
    return 0


def f_b1b_not_group(a, b, c):
    for i in range(3):
        if i:
            if not (a or b) and c:
                return i
    return 0


def f_b1b_body_before_cond(a, b, c):
    for i in range(3):
        acc = i * 2
        if a and b or c:
            return acc
    return 0


def f_b1b_import_prefix(a, b):
    import math
    for i in range(2):
        if i and (a or b):
            return math.trunc(i)
    return 0


def f_b1b_none_check_prefix(a, b):
    for i in range(3):
        s = str(i)
        if s is None or a:
            if i:
                return s
    return 0


def f_b1b_loop_body_chain(a, b, c):
    n = 0
    while n < 3:
        if a and b or c:
            n += 1
        else:
            n += 2
    return n


def f_b1b_loop_header_cond(a, b, c):
    n = 0
    while a and b or c:
        n += 1
        if n > 2:
            break
    return n


def f_b1b_ifexp_trueval(a, b, c):
    for i in range(3):
        if i:
            return (a and b) if c else (a or b)
    return 0


def f_b1b_elif_mixed(a, b, c):
    for i in range(4):
        if a and b:
            return 1
        elif b or c:
            return 2
        elif a or (b and c):
            return 3
    return 0
'''

NE01 = '''\
# ne01: G1 负对照——平坦均匀链与已知工作分组形态（预期 MATCH）
def n_flat_or(a, b, c):
    for i in range(3):
        if i:
            return a or b or c
    return 0


def n_flat_and(a, b, c):
    for i in range(3):
        if i:
            return a and b and c
    return 0


def n_grouped_pair(a, b, c, d):
    for i in range(3):
        if i:
            return (a or b) and (c or d)
    return 0


def n_simple_two(a, b):
    for i in range(3):
        if i:
            return a and b
    return 0
'''

# ────────────────────────────────────────────────────────────────────
# G2 IfExp 三元
# ────────────────────────────────────────────────────────────────────

E04 = '''\
# e04: IfExp 三元——链式/BoolOp 分组交叉/Call 实参/返回值/推导式条件/默认参数/深宿主
def f_chain_ternary(a, b, c, d, e):
    for i in range(3):
        if i:
            while i:
                return a if b else (c if d else e)
    return 0


def f_ternary_deep_right(a, b, c, d, e, f, g):
    for i in range(3):
        if i:
            while i:
                return a if b else (c if d else (e if f else g))
    return 0


def f_ternary_boolop_group(a, b, c, d, e):
    for i in range(3):
        if i:
            while i:
                return (a or b) if c else (d and e)
    return 0


def f_ternary_call_arg(a, b, c):
    def sink(x):
        return x * 2
    for i in range(3):
        if i:
            while i:
                return sink(a if b else c)
    return 0


def f_ternary_return(a, b, c):
    for i in range(3):
        if i:
            while i:
                return a if b else c
    return 0


def f_ternary_comp_value(a, b, xs):
    for i in range(2):
        if i:
            return [x if b else -x for x in xs]
    return []


def f_ternary_comp_cond(a, b, xs):
    for i in range(2):
        if i:
            return [x for x in xs if (x if b else 0)]
    return []


def f_ternary_default_arg(a, b):
    def inner(x, y=(1 if b else 2)):
        return x + y
    for i in range(2):
        if i:
            return inner(a)
    return 0


def f_ternary_subscript(a, b, xs):
    for i in range(3):
        if i:
            while i:
                return xs[a if b else 0]
    return 0


def f_ternary_dict_value(a, b, c):
    for i in range(3):
        if i:
            while i:
                return {'k': a if b else c}
    return {}


def f_ternary_walrus_rhs(a, b, c):
    for i in range(3):
        if i:
            while i:
                return (q := a if b else c) + q
    return 0


def f_ternary_as_cond(a, b, c, xs):
    for i in range(3):
        if (a if b else c) in xs:
            while i:
                return i
    return 0


def f_ternary_nested_in_boolop(a, b, c, d):
    for i in range(3):
        if i:
            while i:
                return (a if b else c) and d
    return 0
'''

NE02 = '''\
# ne02: G2 负对照——浅层三元（预期 MATCH）
def n_simple_ternary(a, b, c):
    if a:
        pass
    return b if a else c


def n_ternary_two_level(a, b, c, d):
    return a if b else (c if d else 0)
'''

# ────────────────────────────────────────────────────────────────────
# G3 Compare 链 + 操作符叶子
# ────────────────────────────────────────────────────────────────────

E05 = '''\
# e05: Compare 链——6 级链/链中嵌 BinOp/Subscript/is-in-notin 冷门叶/条件位/海象值
def f_compare_chain6(a, b, c, d, e, f):
    for i in range(3):
        if i:
            while i:
                return a < b <= c < d <= e < f
    return False


def f_compare_binop_inside(a, b, c, d):
    for i in range(3):
        if i:
            while i:
                return a + 1 < b * 2 <= c - d
    return False


def f_compare_subscript_inside(xs, i, j):
    for k in range(3):
        if k:
            while k:
                return xs[0] < xs[i + 1] <= xs[j]
    return False


def f_compare_is_chain(a, b, c):
    for i in range(3):
        if i:
            while i:
                return a is b is not c
    return False


def f_compare_in_chain(a, b, c):
    for i in range(3):
        if i:
            while i:
                return a in b not in c
    return False


def f_compare_in_cond(a, b, c, d):
    for i in range(3):
        if a < b <= c:
            while i:
                return c > d
    return False


def f_compare_walrus_value(a, b, c):
    for i in range(3):
        if i:
            if (ok := a < b <= c):
                return ok
    return False


def f_compare_mixed_ops(a, b, c, d):
    for i in range(3):
        if i:
            while i:
                return (a == b) < (c != d)
    return False


def f_compare_chain_deep_host(a, b, c, xs):
    try:
        for i in range(3):
            if i:
                while len(xs) < 8:
                    return b <= c < i
    except ValueError:
        return False
    return False


def f_compare_notin_chain(a, b, c):
    for i in range(3):
        if i:
            while i:
                return a not in b in c
    return False
'''

E06 = '''\
# e06: 操作符叶子全遍历——BinOp 13 + Compare 16 + UnaryOp 4（Add..NotIn + USub/UAdd/Invert/Not）
def f_binop_arith(a, b):
    for i in range(3):
        if i:
            while i:
                return (a + b) - (a * b) / (b % a)
    return 0


def f_binop_cold_leaves(a, b):
    for i in range(3):
        if i:
            while i:
                return (a ** b ** 2, a // b, a << b, a >> b)
    return 0


def f_binop_bitwise(a, b):
    for i in range(3):
        if i:
            while i:
                return (a & b) | (a ^ b)
    return 0


def f_binop_matmult(a, b):
    for i in range(3):
        if i:
            while i:
                return a @ b
    return 0


def f_unary_double_neg(a, b):
    for i in range(3):
        if i:
            while i:
                return -a - -b
    return 0


def f_unary_invert_uadd(a):
    for i in range(3):
        if i:
            while i:
                return ~a + (+a) + -(-a)
    return 0


def f_unary_not_chain(a, b, c):
    for i in range(3):
        if i:
            while i:
                return not a + (not b) + (not not c)
    return 0


def f_compare16_full(a, b, c, xs):
    for i in range(3):
        if i:
            while i:
                return (a == b, a != b, a < b, a <= b, a > b, a >= b,
                        a is b, a is not b, a in xs, a not in xs,
                        b == c, b != c, c < a, c <= a, c > b, c >= b)
    return 0


def f_pow_right_assoc(a):
    for i in range(3):
        if i:
            while i:
                return 2 ** 3 ** 2 + a
    return 0


def f_floor_div_shift(a, b):
    for i in range(3):
        if i:
            while i:
                return (-a) // 2 + (b << 1) + (1 << 2 << 3)
    return 0


def f_ops_in_containers(a, b, c):
    for i in range(3):
        if i:
            while i:
                return [a + b, (a - c, {a * b}, {a: b | c})]
    return 0


def f_ops_as_call_args(a, b):
    def sink(x, y):
        return x - y
    for i in range(3):
        if i:
            while i:
                return sink(a << b, a >> b)
    return 0
'''

NE03 = '''\
# ne03: G3 负对照——浅层比较与操作符（预期 MATCH）
def n_simple_compare(a, b):
    return a < b


def n_simple_binop(a, b):
    return a + b * 2 - 1


def n_simple_unary(a):
    return -a
'''

# ────────────────────────────────────────────────────────────────────
# G4 BinOp/UnaryOp/Starred/Slice/Subscript/容器字面量
# ────────────────────────────────────────────────────────────────────

E07 = '''\
# e07: 星号解包 Call/赋值、切片嵌套下标、容器嵌套 >=3 层、深宿主
def f_star_call(a, rest, kw):
    def sink(x, *rs, flag=False, **ks):
        return x + sum(rs) + (1 if flag else 0) + len(ks)
    for i in range(3):
        if i:
            while i:
                return sink(a, *rest, flag=True, **kw)
    return 0


def f_star_call_mixed(a, rest, kw):
    def sink(x, y, *rs, z=1, **ks):
        return x + y + sum(rs) + z + len(ks)
    for i in range(3):
        if i:
            while i:
                return sink(a, 2, *rest, z=3, **kw)
    return 0


def f_star_assign(xs):
    for i in range(3):
        if i:
            while i:
                a, *b = xs
                return a, b
    return 0


def f_star_assign_head(xs):
    for i in range(3):
        if i:
            while i:
                *a, b = xs
                return a, b
    return 0


def f_star_assign_mid(xs):
    for i in range(3):
        if i:
            while i:
                a, *b, c = xs
                return a, b, c
    return 0


def f_slice_nested_sub(m, i, j):
    for k in range(3):
        if k:
            while k:
                return m[i:j, k] + m[1:2, 3]
    return 0


def f_slice_steps(xs, w):
    for i in range(3):
        if i:
            while i:
                return xs[::-1] + xs[:: w] + xs[1 : -1 : 2]
    return 0


def f_slice_expr_bounds(xs, a, b):
    for i in range(3):
        if i:
            while i:
                return xs[a + 1 : b * 2] + xs[a if b else 0 : 3]
    return 0


def f_container_nest3(d):
    for i in range(3):
        if i:
            while i:
                return {'a': [1, (2, {3, 4})], 'b': {'c': [5, 6]}}[d]
    return 0


def f_container_mixed(a, b):
    for i in range(3):
        if i:
            while i:
                return ([a, (b, [a])], {a: {b: [1, 2]}}, {a, (b,)})
    return 0


def f_subscript_deep(m, i, j):
    for k in range(3):
        if k:
            while k:
                return m[i][j][k] + m[i][j : k]
    return 0


def f_tuple_in_call(a, b, c):
    def sink(t):
        return sum(t)
    for i in range(3):
        if i:
            while i:
                return sink((a, b, c)) + sink([a, b])
    return 0
'''

NE04 = '''\
# ne04: G4 负对照——浅层切片/容器/星号（预期 MATCH）
def n_simple_slice(xs):
    return xs[1:3]


def n_simple_container(a, b):
    return [a, (b, 1)], {a: b}


def n_simple_star(xs):
    a, *b = xs
    return a, b
'''

# ────────────────────────────────────────────────────────────────────
# G5 Lambda
# ────────────────────────────────────────────────────────────────────

E08 = '''\
# e08: Lambda——闭包捕获/默认参/返回值/排序 key/装饰器工厂/三元 boolop 体/深宿主
def f_lambda_closure(k):
    fn = lambda x: x + k
    for i in range(3):
        if i:
            while i:
                return fn(i)
    return 0


def f_lambda_default(k):
    fn = lambda x, y=2: x * y + k
    for i in range(3):
        if i:
            while i:
                return fn(i, y=3)
    return 0


def f_lambda_return_factory(k):
    def make():
        return lambda x: x + k
    for i in range(3):
        if i:
            while i:
                return make()(i)
    return 0


def f_lambda_sort_key(pairs):
    for i in range(3):
        if i:
            while i:
                return sorted(pairs, key=lambda p: p[1])
    return 0


def f_lambda_deco_factory(fn):
    def deco(f):
        return lambda *a, **k: f(*a, **k) + 1
    wrapped = deco(fn)
    for i in range(3):
        if i:
            while i:
                return wrapped(i)
    return 0


def f_lambda_body_ternary(a, b):
    fn = lambda x: x if x > 0 else -x
    for i in range(3):
        if i:
            while i:
                return fn(a) + fn(b)
    return 0


def f_lambda_body_boolop(a, b, d):
    fn = lambda x: x or a
    gn = lambda x: x and b
    for i in range(3):
        if i:
            while i:
                return fn(a) + gn(d)
    return 0


def f_lambda_immediate(a):
    for i in range(3):
        if i:
            while i:
                return (lambda x: x + 1)(a)
    return 0


def f_lambda_in_dict(a):
    ops = {'add': lambda x: x + 1, 'mul': lambda x: x * 2}
    for i in range(3):
        if i:
            while i:
                return ops['add'](a) + ops['mul'](a)
    return 0


def f_lambda_nested(a, b):
    fn = lambda x: lambda y: x + y
    for i in range(3):
        if i:
            while i:
                return fn(a)(b)
    return 0


def f_lambda_default_ternary(a, b):
    fn = lambda x, y=(1 if b else 2): x + y
    for i in range(3):
        if i:
            while i:
                return fn(a)
    return 0


def f_lambda_starargs(a, rest):
    fn = lambda *args: sum(args) + a
    for i in range(3):
        if i:
            while i:
                return fn(*rest)
    return 0
'''

NE05 = '''\
# ne05: G5 负对照——浅层 lambda（预期 MATCH）
def n_simple_lambda(a):
    fn = lambda x: x + 1
    return fn(a)


def n_lambda_sort(pairs):
    return sorted(pairs, key=lambda p: p[0])
'''

# ────────────────────────────────────────────────────────────────────
# G6 推导式族
# ────────────────────────────────────────────────────────────────────

E09 = '''\
# e09: 推导式族——四形/嵌套推导/多 for+条件/海象/三元/await/唯一实参（comprehension 管线）
def f_listcomp_deep(a, xs):
    for i in range(2):
        if i:
            while i:
                return [x + a for x in xs]
    return []


def f_setcomp_deep(a, xs):
    for i in range(2):
        if i:
            while i:
                return {x % a for x in xs}
    return set()


def f_dictcomp_deep(a, xs):
    for i in range(2):
        if i:
            while i:
                return {x: x + a for x in xs}
    return {}


def f_genexp_deep(a, xs):
    for i in range(2):
        if i:
            while i:
                return sum(x + a for x in xs)
    return 0


def f_nested_comp(m):
    for i in range(2):
        if i:
            while i:
                return [[y for y in row] for row in m]
    return []


def f_nested_dictcomp(d):
    for i in range(2):
        if i:
            while i:
                return {k: [v for v in vs] for k, vs in d.items()}
    return {}


def f_multi_for(a, b):
    for i in range(2):
        if i:
            while i:
                return [x * y for x in a for y in b]
    return []


def f_multi_for_cond(a, b):
    for i in range(2):
        if i:
            while i:
                return [x * y for x in a if x > 0 for y in b if y < 3]
    return []


def f_comp_walrus(xs):
    def g(x):
        return x + 1
    for i in range(2):
        if i:
            while i:
                return [y for x in xs if (y := g(x)) > 1]
    return []


def f_comp_ternary(a, xs):
    for i in range(2):
        if i:
            while i:
                return [x if a else -x for x in xs]
    return []


def f_comp_sole_arg(xs):
    def sink(v):
        return v
    for i in range(2):
        if i:
            while i:
                return sink([x for x in xs])
    return 0


def f_comp_in_comp(a, xs):
    for i in range(2):
        if i:
            while i:
                return {x: [y for y in xs if y > x] for x in a}
    return {}
'''

E09B = '''\
# e09b: async 推导式（B96 已封闭面回归）——await in comprehension / async for comp
async def a_one(ait, xs):
    async for i in ait():
        if i:
            return [await g2(x) for x in xs if x]
    return []


async def a_two(ait, xs):
    async with acm():
        return [x async for x in ait()]
    return []


async def a_three(ait, d):
    acc = []
    async for i in ait():
        if i:
            acc.extend({k: await g2(v) for k, v in d.items() if v})
    return acc


async def a_four(ait, xs):
    async for i in ait():
        if i:
            return sum(1 for x in xs if await g2(x))
    return 0


class acm:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *e):
        return False


async def g2(x):
    return x
'''

NE06 = '''\
# ne06: G6 负对照——浅层推导式（预期 MATCH）
def n_simple_listcomp(xs):
    return [x for x in xs]


def n_simple_dictcomp(xs):
    return {x: x for x in xs}


def n_simple_genexp(xs):
    return sum(x for x in xs)
'''

# ────────────────────────────────────────────────────────────────────
# G7 Call/keyword_args/star_args
# ────────────────────────────────────────────────────────────────────

E10 = '''\
# e10: Call/keyword/star_args——kwargs 混位置/*args/**kwargs 混合/生成器调用链/方法链深嵌
class Chain:
    def a(self):
        return self

    def b(self):
        return self

    def c(self):
        return 1


def f_kwargs_mixed(a, b, c, d):
    def sink(w, x, y=0, z=0):
        return w + x + y + z
    for i in range(3):
        if i:
            while i:
                return sink(a, b, y=c, z=d)
    return 0


def f_starargs_mixed(a, rest):
    def sink(x, *rs):
        return x + sum(rs)
    for i in range(3):
        if i:
            while i:
                return sink(a, *rest, 3)
    return 0


def f_dstar_mixed(a, kw):
    def sink(x, b=0, c=0):
        return x + b + c
    for i in range(3):
        if i:
            while i:
                return sink(a, b=1, **kw)
    return 0


def f_both_star_dstar(a, rest, kw):
    def sink(x, *rs, y=0, **ks):
        return x + sum(rs) + y + len(ks)
    for i in range(3):
        if i:
            while i:
                return sink(a, *rest, y=2, **kw)
    return 0


def f_call_chain(a):
    def h(x):
        return x - 1

    def g(x):
        return x * 2
    for i in range(3):
        if i:
            while i:
                return h(g(h(a)))
    return 0


def f_method_chain(a):
    obj = Chain()
    for i in range(3):
        if i:
            while i:
                return obj.a().b().c() + a
    return 0


def f_call_lambda_arg(a):
    for i in range(3):
        if i:
            while i:
                return sorted([a, 2, 1], key=lambda x: -x)
    return 0


def f_call_comp_arg(xs):
    for i in range(3):
        if i:
            while i:
                return sum([x for x in xs], 10)
    return 0


def f_deco_with_args(a):
    def deco(n):
        def wrap(fn):
            def inner(x):
                return fn(x) + n
            return inner
        return wrap

    @deco(3)
    def base(x):
        return x * 2
    for i in range(3):
        if i:
            while i:
                return base(a)
    return 0


def f_gen_call_chain(a, xs):
    def g():
        yield from xs
    for i in range(3):
        if i:
            while i:
                return list(g()) + [a]
    return 0


def f_kwargs_deep_host(a, b, c):
    def sink(x, y=0, z=0):
        return x + y + z
    try:
        for i in range(3):
            if i:
                while i:
                    return sink(a, y=b, z=c)
    except ValueError:
        return -1
    return 0


def f_call_ternary_arg(a, b, c):
    def sink(x):
        return x + 1
    for i in range(3):
        if i:
            while i:
                return sink(a if b else c)
    return 0
'''

NE07 = '''\
# ne07: G7 负对照——浅层调用（预期 MATCH）
def n_simple_call(a, b):
    return max(a, b)


def n_simple_kwargs(a):
    def sink(x, y=1):
        return x + y
    return sink(a, y=2)


def n_simple_star(a, rest):
    def sink(x, *rs):
        return x + sum(rs)
    return sink(a, *rest)
'''

# ────────────────────────────────────────────────────────────────────
# G8 JoinedStr/FormattedValue + fstring_conversion
# ────────────────────────────────────────────────────────────────────

E11 = '''\
# e11: f-string——!r/!s/!a 转换符、嵌套 format-spec（B90 回归）、f 嵌 f、深宿主值
def f_conv_rsa(a, b, c):
    for i in range(3):
        if i:
            while i:
                return f'{a!r} {b!s} {c!a}'
    return ''


def f_spec_nested(a, w):
    for i in range(3):
        if i:
            while i:
                return f'{a:>{w}}'
    return ''


def f_spec_nested_call(a, b):
    for i in range(3):
        if i:
            while i:
                return f'{a:>{len(str(b))}}'
    return ''


def f_spec_conv_combo(a):
    for i in range(3):
        if i:
            while i:
                return f'{a!r:>10}' + f'{a!s:<8}'
    return ''


def f_fstring_in_fstring(a):
    for i in range(3):
        if i:
            while i:
                return f'[{f"{a}"}]'
    return ''


def f_fstring_expr(a, b):
    for i in range(3):
        if i:
            while i:
                return f'{a + b * 2} and {a if b else 0}'
    return ''


def f_fstring_concat(a, b):
    for i in range(3):
        if i:
            while i:
                return f'a{a}' f'b{b}' 'plain'
    return ''


def f_fstring_deep_host(a):
    try:
        for i in range(3):
            if i:
                while i:
                    log = f'v={a!r},i={i}'
                    return log
    except ValueError:
        return ''
    return ''


def f_fstring_in_dict(a):
    for i in range(3):
        if i:
            while i:
                return {'msg': f'{a!s}'}
    return {}


def f_fstring_call_in_spec(a, b):
    for i in range(3):
        if i:
            while i:
                return f'{a:0{b}d}|{a:>{b + 1}}'
    return ''


def f_fstring_method_call(a):
    for i in range(3):
        if i:
            while i:
                return f'{a.upper()}|{str(a)!r}'
    return ''


def f_fstring_cond_value(a, b):
    for i in range(3):
        if i:
            while i:
                return f'result={a if b else "none"}'
    return ''
'''

NE08 = '''\
# ne08: G8 负对照——浅层 f-string（预期 MATCH）
def n_simple_fstring(a):
    return f'{a}'


def n_simple_conv(a):
    return f'{a!r}'
'''

# ────────────────────────────────────────────────────────────────────
# G9 Await/Yield/YieldFrom
# ────────────────────────────────────────────────────────────────────

E12 = '''\
# e12: Await/Yield/YieldFrom 表达式位（B95/B96 已封闭面回归）
async def f_await_assign_rhs(a, src):
    async with acm9():
        for i in range(3):
            if i:
                v = await src(i)
                return v
    return 0


async def f_await_return(a, src):
    async for i in src(a):
        if i:
            return await src(i)
    return 0


async def f_await_cond_pos(a, src):
    async for i in src(a):
        if await src(i):
            return i
    return 0


async def f_await_call_arg(a, src):
    def sink(x):
        return x + 1
    async for i in src(a):
        if i:
            return sink(await src(i))
    return 0


async def f_await_deep3(a, src):
    async with acm9():
        async for i in src(a):
            if i:
                return (await src(i)) + 1
    return 0


async def f_await_boolop(a, src):
    async for i in src(a):
        if (await src(i)) or a:
            return i
    return 0


def f_yield_expr_arg(xs):
    def sink(x):
        return x
    for i in range(3):
        if i:
            yield sink((yield i))
    return


def f_yield_assign_rhs(xs):
    for i in range(3):
        if i:
            v = yield i
            if v:
                yield v
    return


def f_yield_from_chain(xs):
    def inner():
        yield from xs
    for i in range(3):
        if i:
            yield from inner()
    return


def f_yield_from_deep(xs):
    def lvl2():
        yield from xs
        return

    def lvl1():
        for i in range(2):
            if i:
                yield from lvl2()
    for j in range(2):
        if j:
            yield from lvl1()
    return


def f_yield_in_boolop(xs):
    for i in range(3):
        if i:
            yield (yield i) or 0
    return


class acm9:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *e):
        return False
'''

NE09 = '''\
# ne09: G9 负对照——浅层 await/yield（预期 MATCH）
async def n_simple_await(src):
    return await src(1)


def n_simple_yield(xs):
    for x in xs:
        yield x


def n_simple_yield_from(xs):
    yield from xs
'''

# ────────────────────────────────────────────────────────────────────
# G10 NamedExpr 海象
# ────────────────────────────────────────────────────────────────────

E13 = '''\
# e13: 海象——while/if 条件、推导式条件、lambda 默认参、海象链、RHS 三元/boolop
def f_walrus_while_cond(xs):
    it = iter(xs)
    acc = []
    while (chunk := next(it, None)) is not None:
        for i in range(2):
            if i:
                acc.append(chunk)
    return acc


def f_walrus_if_cond(a):
    for i in range(3):
        if (n := len(a)) > 2:
            while i:
                return n
    return 0


def f_walrus_comp_cond(xs):
    def g(x):
        return x + 1
    for i in range(2):
        if i:
            while i:
                return [y for x in xs if (y := g(x)) > 1]
    return []


def f_walrus_lambda_default(a):
    fn = lambda x, y=(z := 2): x + y + z
    for i in range(3):
        if i:
            while i:
                return fn(a)
    return 0


def f_walrus_chain(a):
    for i in range(3):
        if i:
            while i:
                return (p := (q := (r := a) + 1) + 2) + p + q + r
    return 0


def f_walrus_rhs_ternary(a, b, c):
    for i in range(3):
        if i:
            while i:
                return (w := a if b else c) + w
    return 0


def f_walrus_rhs_boolop(a, b, c):
    for i in range(3):
        if i:
            while i:
                return (w := (a or b) and c) + w
    return 0


def f_walrus_call_arg(a):
    def sink(x):
        return x + 1
    for i in range(3):
        if i:
            while i:
                return sink((x := a)) + x
    return 0


def f_walrus_deep_host(a, b):
    try:
        for i in range(3):
            if i:
                while i:
                    if (v := a + b) > 1:
                        return v
    except ValueError:
        return -1
    return 0


def f_walrus_in_while_body(a, xs):
    n = 0
    while n < 3:
        for i in range(2):
            if (m := i + a) > 2:
                n += m
    return n


def f_walrus_elif_chain(a):
    for i in range(4):
        if (k := i * a) > 3:
            return k
        elif k > 1:
            return -k
    return 0


def f_walrus_genexp_cond(a, xs):
    for i in range(2):
        if i:
            while i:
                return sum(1 for x in xs if (y := x + a) > 1)
    return 0
'''

NE10 = '''\
# ne10: G10 负对照——浅层海象（预期 MATCH）
def n_simple_walrus(a):
    if (n := a) > 0:
        return n
    return 0


def n_walrus_while(xs):
    it = iter(xs)
    while (c := next(it, None)) is not None:
        return c
    return None
'''

PROBES = [
    ('e01_g1_b98_matrix.py', E01),
    ('e02_g1_b98_hosts.py', E02),
    ('e03_g1_b1b_stress.py', E03),
    ('ne01_g1_neg.py', NE01),
    ('e04_g2_ifexp_deep.py', E04),
    ('ne02_g2_neg.py', NE02),
    ('e05_g3_compare_chain.py', E05),
    ('e06_g3_op_leaves.py', E06),
    ('ne03_g3_neg.py', NE03),
    ('e07_g4_star_slice_containers.py', E07),
    ('ne04_g4_neg.py', NE04),
    ('e08_g5_lambda_deep.py', E08),
    ('ne05_g5_neg.py', NE05),
    ('e09_g6_comprehensions.py', E09),
    ('e09b_g6_async_comps.py', E09B),
    ('ne06_g6_neg.py', NE06),
    ('e10_g7_call_args.py', E10),
    ('ne07_g7_neg.py', NE07),
    ('e11_g8_fstrings.py', E11),
    ('ne08_g8_neg.py', NE08),
    ('e12_g9_await_yield.py', E12),
    ('ne09_g9_neg.py', NE09),
    ('e13_g10_walrus.py', E13),
    ('ne10_g10_neg.py', NE10),
]


def main():
    written = []
    for name, src in PROBES:
        path = os.path.join(HERE, name)
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(src)
        import ast
        ast.parse(src)
        written.append(name)
    print('generated %d probes:' % len(written))
    for n in written:
        print('  ', n)


if __name__ == '__main__':
    main()
