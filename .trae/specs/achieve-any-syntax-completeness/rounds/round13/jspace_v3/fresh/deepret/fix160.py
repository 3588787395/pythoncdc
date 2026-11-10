# fix160.py: rr-v5r160 [v160-DEEPRET] 深层循环内 return 的 N 对帧清理泛化
# （只增不破，单文件一处——泛化匹配插在 RC3 之前）。
#
# F1: 三层循环内 `return authinfo`（urllib.request.HTTPPasswordMgr.
#     find_user_password 实形，源 line 850-858）v159 渲染裸 Expr `authinfo`
#     ——return 关键字丢失=真实 R1（函数永不返回 authinfo）。
#
# 根因: CPython 3.11 对 k 层循环内的 `return X` 发射 <eval X> + (SWAP(2);
#     POP_TOP)×k + RETURN_VALUE——每对弹一层循环迭代器帧，返回值驻留栈底被
#     RETURN_VALUE 消费（deep3 B124=[LOAD, (SWAP,POP)×3, RETURN] 单块）。主语
#     句循环的 RC2 只认 1/2 对且不设 skip_initial_pop（2 对形靠 Expr-flush +
#     R23-N6 促销自愈）；RC3（deferred）先于一切命中 k=3 首对但只 skip 一个
#     POP（skip_initial_pop=True）→ 第二个 POP 被 Expr-flush；第三对 SWAP 因
#     stmt_instrs 已空被追加进缓冲 → 残留破坏促销判据 → Return 值丢失。
#
# 修复: RC2 两形之后、RC3 之前插入 [v160-DEEPRET] 泛化 N 对精确匹配——剩余段
#     = POP_TOP + (SWAP + POP_TOP)* + RETURN_VALUE → 跳过 SWAP 并设
#     skip_initial_pop=(对数+1)//2（RETURN 前全部 POP 由计数器消费）；剩余段
#     直邻 RETURN_VALUE（内层对的 SWAP，其 POP 已由上层 skip 计数消费）→ 跳
#     过 SWAP。RC3（intervening 清理段延迟形）与其后路径逐位保留；既有 1/2
#     对形由 RC2 先命中逐位不变；不命中逐字节落回现状（C3）。2 对形对照在新
#     路径下 stmt_instrs=[值] 直达 Return，渲染与既有促销路径产物逐字相同。
import io

PATH = r'F:/Downloads/pythoncdc-main/core/cfg/region_ast_generator.py'
MARKER = 'v160-DEEPRET'

s = io.open(PATH, encoding='utf-8-sig').read()
orig = s

anchor = "                # [RC3 fix] SWAP(2) + POP_TOP with deferred RETURN_VALUE in"
assert s.count(anchor) == 1, 'anchor %d' % s.count(anchor)

insertion = """                # [v160-DEEPRET] 泛化 N 对循环帧清理精确匹配（只增不破，
                # 先于 RC3）：k 层循环内 `return X` 的剩余段 = POP_TOP +
                # (SWAP + POP_TOP)*(k-1) + RETURN_VALUE——每对 SWAP(2)+POP_TOP
                # 弹一层迭代器帧，返回值驻留栈底被 RETURN_VALUE 消费
                # （HTTPPasswordMgr.find_user_password 三层 for 实形，k=3）。
                # RC2 只认 1/2 对且不设 skip_initial_pop（2 对形靠 Expr-flush +
                # R23-N6 促销自愈）；RC3 对 k=3 首对只 skip 一个 POP（
                # skip_initial_pop=True）→ 第二个 POP 被 Expr-flush、第三对
                # SWAP 落入语句缓冲破坏促销 → Return 值丢失=真实 R1。命中即
                # 跳过 SWAP 并设 skip_initial_pop=(对数+1)//2（RETURN 前全部
                # POP 由计数器消费，不落 Expr-flush）；POP 后直邻 RETURN 的
                # 内层 SWAP 同为帧清理跳过。RC2 两形先命中逐位不变；RC3
                # （intervening 清理段延迟形）与其后路径逐位保留；不命中逐字
                # 节落回现状（C3）。
                if (not _rc2_skip_swap
                        and len(_rc2_swap_rem) >= 2
                        and _rc2_swap_rem[0].opname == 'POP_TOP'):
                    _v160_i = 1
                    while (_v160_i + 1 < len(_rc2_swap_rem)
                           and _rc2_swap_rem[_v160_i].opname == 'SWAP'
                           and _rc2_swap_rem[_v160_i + 1].opname == 'POP_TOP'):
                        _v160_i += 2
                    if _v160_i < len(_rc2_swap_rem) and _rc2_swap_rem[_v160_i].opname in ('RETURN_VALUE', 'RETURN_CONST'):
                        _rc2_skip_swap = True
                        skip_initial_pop = (_v160_i + 1) // 2
                if (not _rc2_skip_swap
                        and len(_rc2_swap_rem) >= 1
                        and _rc2_swap_rem[0].opname in ('RETURN_VALUE', 'RETURN_CONST')):
                    _rc2_skip_swap = True
"""

s = s.replace(anchor, insertion + anchor, 1)

assert s != orig
assert s.count(MARKER) == 1
io.open(PATH, 'w', encoding='utf-8-sig', newline='').write(s)
print('fix160 applied: %d marker' % s.count(MARKER))

import py_compile
py_compile.compile(PATH, doraise=True)
print('syntax OK')
