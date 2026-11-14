# fix161.py: rr-v5r161 [v161-NOTMIX] 融合 not or→and 混合链族（只增不破，单文件
# 五处标记——走查状态初始化 + 三道断链门的融合头甄别 + 走查尾极性重分类）。
#
# F1: `if not host or (not port and _safe_gethostbyname(host) in self.get_names()):`
#     （urllib.request.FileHandler.open_local_file 实形，源 line 1514-1515；
#     最小形 `if not a or (b and c):`）v160 渲染 `if host: if not port and ...:`
#     ——factored 形=真实 R1（语义反转：¬A 时源码进体、渲染跳过——判官
#     Different control flow）。
#
# 根因: CPython 对 or 链首成员 `not A` 做极性融合——不发射 UNARY_NOT，直接以
#     POP_JUMP_FORWARD_IF_FALSE 直跳条件真值汇聚块（body）。or→and 混合链
#     `not A or (B and C)` 的操作数块=[A IF_FALSE→body; B IF_FALSE→exit;
#     C IF_FALSE→exit]（c 实形第二成员 `not port` 为 IF_TRUE→exit）。主条件
#     链走查（_detect_boolop_conditional_chain）的 opcode-only 分类把链首
#     误标 'and'，三道既有断链门都以「链首是真 and 头（其 FALSE 目标=共享
#     exit）」为前提把续接候选斩断：b 形（FALSE 候选）死于 [W14-A 真/假出口
#     目标对判据]（cand exit ≠ T0=body）、c 形（TRUE 候选）死于 [R3-K 读法
#     (b)]（候选真目标 exit ≠ 成功汇聚 T0）、续接后的 and 子链成员死于
#     [R53-A 同算子 run 出口一致性]（run 头=链首、jt=body ≠ 成员 exit）。
#     链首走查死亡后 wrapper 从 B6 重试装配 [(6,'and'),(10,'and')] 内层
#     and 区，链首 A 落入独立 IfRegion → `if a: if b and c:` factored 反转。
#
# 修复: 走查新增融合头状态 _v161_or_head_exit——首续接（len(chain)==1）候选
#     与链首目标不等时把候选自身跳转目标登记为 and 子链共享出口并放行
#     （b 形=W14-A 门、c 形=R3-K 门）；后续成员目标与登记出口一致即放行
#     （W14-A 门 + R53-A 豁免），不一致维持断链。走查尾精确形甄别：链首
#     'and'+FALSE 极性 ∧ 链首目标=末成员 fall-through（条件真值 merge）∧
#     其余成员跳转目标两两等价于登记出口且 ≠ 链首目标 → 链首重分类 'or'、
#     子链成员统一 'and'（IF_TRUE 成员由构建层 implicit-not 还原 `not X`，
#     与 W14-A 同目标归一同一理据）→ 既有 or→and 边界 _try_unify 路径
#     （`A or (B and C)` 判官 Equal 同构实证）。甄别不成立（嵌套 if-else：
#     链首 FALSE 目标=外层 else ≠ 末成员 fall-through；全 and 链：目标同块；
#     多融合 not or 链：成员目标不唯一）走查尾既有 None 路径逐位复原（C3）；
#     登记不发生（a_not_or 等既有形）走查逐字节不变。
import io

PATH = r'F:/Downloads/pythoncdc-main/core/cfg/region_analyzer.py'
MARKER = 'v161-NOTMIX'

s = io.open(PATH, encoding='utf-8-sig').read()
orig = s
N = 0


def rep(old, new, expect=1):
    global s, N
    c = s.count(old)
    assert c == expect, 'anchor count %d (expect %d): %r' % (c, expect, old[:80])
    s = s.replace(old, new, expect)
    N += 1


# [1] 走查状态初始化（walk 循环前）
rep("""                        _b115_loop_guard_map[_b115_cb] = _b115_lr
        while current and current.start_offset not in visited:""",
"""                        _b115_loop_guard_map[_b115_cb] = _b115_lr
        # [v161-NOTMIX] 融合 not or→and 混合链走查状态：or 链首 `not A` 被
        # CPython 极性融合（POP_JUMP_FORWARD_IF_FALSE 直跳条件真值汇聚块），
        # opcode-only 分类误标 'and'。首续接候选与链首目标不等时，本状态登记
        # 候选自身跳转目标 = and 子链共享 false-exit，后续成员目标与之一致即
        # 放行（三道断链门的甄别见各标记处）；走查尾按精确形重分类链首极性。
        # 登记不发生（无融合头的既有链形）全部门维持原行为逐字节不变（C3）。
        _v161_or_head_exit = None
        while current and current.start_offset not in visited:""")
N = N  # noqa

# [2] [W14-A 真/假出口目标对判据] 断链门：b 形（FALSE 候选）首续接识别 + 一致放行
rep("""                    if (_w14_t0 is not None and _w14_cand_t is not None
                            and _w14_cand_t is not _w14_t0
                            and not self._is_equivalent_exit_block(_w14_t0, _w14_cand_t)):
                        break""",
"""                    if (_w14_t0 is not None and _w14_cand_t is not None
                            and _w14_cand_t is not _w14_t0
                            and not self._is_equivalent_exit_block(_w14_t0, _w14_cand_t)):
                        # [v161-NOTMIX] 融合 not 头甄别（b 形首续接）：链首
                        # `not A`（FALSE→body=条件真值 merge）+ FALSE 候选
                        # （and 子链首成员，FALSE→exit=子链共享 false-exit）。
                        # 「全体成员 FALSE 同出口」的 and 链不变量被链首违反
                        # 且链首目标恰为子链末成员 fall-through 时，链首实为
                        # 极性反转 or 成员——登记子链出口并放行走查（完整形由
                        # 走查尾甄别，不成立则尾部既有 None 路径逐位复原）。
                        # 嵌套 if 条件块（链首 FALSE→外层 else，与末成员
                        # fall-through 不同块）走查尾甄别不命中 → 既有断链
                        # 语义经 None 路径复原。首续接之后的成员：目标与登记
                        # 出口同块 = 子链真实成员，放行；否则维持断链。
                        if len(chain) == 1:
                            _v161_or_head_exit = _w14_cand_t
                        elif (_v161_or_head_exit is None
                                or _w14_cand_t is not _v161_or_head_exit):
                            break""")

# [3] [R3-K IF_TRUE 候选出口一致性校验] 断链门：c 形（TRUE 候选）首续接识别
rep("""                        if not _r3k_or_member:
                            break""",
"""                        if not _r3k_or_member:
                            # [v161-NOTMIX] 融合 not 头甄别（c 形首续接）：
                            # 链首 `not A`（FALSE→body=成功汇聚点）+ TRUE 族
                            # 候选（负极性 and 子链成员 `not X`：真=失败 →
                            # exit=子链共享 false-exit ≠ T0）。读法 (a) 的
                            # 「真目标 ≡ T0」以链首为真 and 头为前提，融合头
                            # 形下 T0=body 是成功汇聚点而非共享出口——候选真
                            # 目标实为子链出口，登记并放行（后续 TRUE 成员
                            # 目标与登记出口一致同放；完整形由走查尾甄别，
                            # 不成立则尾部既有 None 路径逐位复原）。
                            if len(chain) == 1:
                                _v161_or_head_exit = _r3k_cand_t
                            elif not (_v161_or_head_exit is not None
                                      and _r3k_cand_t is _v161_or_head_exit):
                                break""")

# [4] [R53-A 同算子 run 出口一致性] pop 门：融合头子链成员豁免
rep("""                    if (not _normal_or and not _not_or_chain
                            and (not _equivalent_exits or _is_scenario_b_ternary)
                            and not _r53_same_run_exit):
                        chain.pop()
                        break""",
"""                    # [v161-NOTMIX] 融合头子链成员豁免：链首为极性反转
                    # or 成员时，链首所属 run 与 and 子链 run 分属两个操作
                    # 符组——子链成员的真实 run 头是 chain[1]（非链首），
                    # 其共享出口是登记的 _v161_or_head_exit。候选跳转目标与
                    # 登记出口同块 = 该子链 run 的真实成员（与 _r53_same_
                    # run_exit 同一「run 头共享出口」判据，按正确 run 头
                    # 计算）；不成立维持 pop（嵌套条件块不被吸收）。
                    _v161_sub_run_exit = (
                        _v161_or_head_exit is not None
                        and cur_jump_target is _v161_or_head_exit)
                    if (not _normal_or and not _not_or_chain
                            and (not _equivalent_exits or _is_scenario_b_ternary)
                            and not _r53_same_run_exit
                            and not _v161_sub_run_exit):
                        chain.pop()
                        break""")

# [5] 走查尾精确形甄别 + 链首极性重分类（all_same_target 前）
rep("""        all_same_target = True
        target_groups = {}""",
"""        # [v161-NOTMIX] 融合 not 头极性甄别与重分类（走查尾，只增不破）：
        # 精确形 = 链首 'and' 且 FALSE 极性 ∧ 链首跳转目标 = 末成员
        # fall-through（条件真值 merge，`not A` 真边直达体的融合签名）∧
        # 其余成员跳转目标两两等价于登记出口（and 子链共享 false-exit，
        # 含 CPython jump-threading 的等价平凡出口变体）∧ 出口 ≠ 链首
        # 目标（出口=成功汇聚点时为歧义形，维持原判）。命中即链首重分类
        # 'or'（构建层对 or 链 IF_FALSE 成员的极性重建自动渲染 `not X`）、
        # 子链成员统一 'and'（IF_TRUE 成员由构建层 implicit-not 逐项还原，
        # 与 W14-A 同目标归一同一理据）→ 既有 or→and 边界 _try_unify 路径
        # （`A or (B and C)` 判官 Equal 同构实证）。不命中（嵌套 if-else：
        # 链首 FALSE 目标=外层 else ≠ 末成员 fall-through；全 and 链：链首
        # 目标=成员出口同块；多融合 not or 链：成员目标不唯一）逐位落回
        # 既有尾部判定（C3）。
        if (len(chain) >= 2
                and chain[0][1] == 'and'
                and _v161_or_head_exit is not None):
            _v161_hblk = chain[0][0]
            _v161_hli = _v161_hblk.get_last_instruction()
            if (_v161_hli is not None
                    and getattr(_v161_hli, 'argval', None) is not None
                    and 'FALSE' in _v161_hli.opname):
                _v161_hjt = self.cfg.get_block_by_offset(_v161_hli.argval)
                _v161_tblk = chain[-1][0]
                _v161_tli = _v161_tblk.get_last_instruction()
                _v161_tft = None
                if (_v161_tli is not None
                        and getattr(_v161_tli, 'argval', None) is not None):
                    _v161_tft = next(
                        (s for s in _v161_tblk.conditional_successors
                         if s.start_offset != _v161_tli.argval), None)
                if (_v161_hjt is not None
                        and _v161_tft is not None
                        and _v161_tft is _v161_hjt
                        and not self._is_equivalent_exit_block(
                            _v161_hjt, _v161_or_head_exit)):
                    _v161_sub_uniform = True
                    for _v161_mblk, _v161_mop in chain[1:]:
                        _v161_mli = _v161_mblk.get_last_instruction()
                        if (_v161_mli is None
                                or getattr(_v161_mli, 'argval', None) is None):
                            _v161_sub_uniform = False
                            break
                        _v161_mjt = self.cfg.get_block_by_offset(_v161_mli.argval)
                        if (_v161_mjt is None
                                or not (_v161_mjt is _v161_or_head_exit
                                        or self._is_equivalent_exit_block(
                                            _v161_mjt, _v161_or_head_exit))):
                            _v161_sub_uniform = False
                            break
                    if _v161_sub_uniform:
                        _v161_new_chain = [(chain[0][0], 'or')]
                        _v161_new_chain.extend(
                            (b, 'and') for b, _ in chain[1:])
                        chain = _v161_new_chain
        all_same_target = True
        target_groups = {}""")

assert s != orig
assert s.count(MARKER) == 5, 'marker count %d' % s.count(MARKER)
io.open(PATH, 'w', encoding='utf-8-sig', newline='').write(s)
print('fix161 applied: %d insertions, %d markers' % (N, s.count(MARKER)))

import py_compile
py_compile.compile(PATH, doraise=True)
print('syntax OK')
