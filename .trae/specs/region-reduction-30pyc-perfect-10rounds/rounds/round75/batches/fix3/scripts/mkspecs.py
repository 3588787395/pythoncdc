# -*- coding: utf-8 -*-
"""R75 fix3 · 由 region_analyzer.py 行号抽取唯一锚点，生成单 edit spec + 合并 spec。

anchors (1-based, inclusive, LF-normalised):
  A  16920-16924  or 链首段极性守卫（IF_NONE）
  B  2258-2267    _is_normal_flow_sink 单块判据 -> 链式闭合死端 + 冲突受限升级门
  B2 17664-17669  _else_has_external_pred 外部前驱区分条件跳入/顺序落入（xp1，已弃用：abde 实测不需要）
  D  19963        在 shared-block merge 段之前插入平坦链判否
  E  18152        or 链成员兄弟区摘除 + 未认领块补 BASIC
合并臂 trym = A+B+D+E（4 edits）。
"""
import io
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

SRC = r'F:\Downloads\pythoncdc-main\core\cfg\region_analyzer.py'
OUT = r'D:\Temp\opencode\r75gate\fix3\specs'
REL = 'core/cfg/region_analyzer.py'


def load():
    raw = io.open(SRC, 'rb').read()
    assert raw[:3] != b'\xef\xbb\xbf', 'region_analyzer must stay BOM-free'
    src = raw.decode('utf-8').replace('\r\n', '\n')
    assert '\r' not in src, 'mixed endings'
    return src, src.split('\n')


def span(lines, a, b, expect=None):
    got = '\n'.join(lines[a - 1:b])
    if expect is not None:
        assert got == expect, 'line span %d-%d drifted:\n%r\nvs\n%r' % (a, b, got, expect)
    return got


def main():
    src, lines = load()

    # ---------------- Edit A ----------------
    a_anchor = span(lines, 16920, 16924,
                    '                if (_main_cond_last is not None\n'
                    '                        and _main_cond_last.opname in (FORWARD_CONDITIONAL_JUMP_OPS | SHORT_CIRCUIT_JUMP_OPS)\n'
                    "                        and ('IF_TRUE' in _main_cond_last.opname\n"
                    "                             or 'IF_FALSE' in _main_cond_last.opname)\n"
                    '                        and _main_cond_last.argval is not None):')
    a_repl = '''                # [R75-FIX3-A] or 短路链首段极性补齐（`is None` 型）。
                # 根因：`if A is None or B is None:` 首段以 POP_JUMP_FORWARD_IF_NONE 短路跳
                #   then、末段以 POP_JUMP_FORWARD_IF_NOT_NONE 跳出到 else，两者的 opcode 名
                #   不含 IF_TRUE/IF_FALSE，原守卫在入口即拒绝，链退化为「`if not A:` 反转 +
                #   嵌套 if」（real_quote.get_real_minute_kline 的 `fq is None or ex_info is
                #   None` 即此形态，产物多一层嵌套且条件翻转）。
                # 同层身份判据：只读首段末条指令的 opcode 名（放行面收窄到 IF_NONE，不放
                #   IF_NOT_NONE——`if x is not None:` 单条件形态不构成 or 链）与其跳转目标；
                #   链体拓扑判据原样保留（成员跳同一 then 入口、成员块无 STORE/POP_TOP、
                #   末段条件跳的目标不是 then 入口且 fall-through 正是 then 入口），嵌套
                #   `if A: if B:` 仍由链尾判据断开；不读名字/常量/偏移阈值/函数名。
                # 去向与守卫：守卫通过才进入原链体行走，任一段不满足拓扑即 break 收链
                #   （len(_or_chain) < 2 不做任何改写）；满足才重定向 condition_block 到
                #   链末并置 _main_inline_boolop_chain，否则维持原判定路径。
                if (_main_cond_last is not None
                        and _main_cond_last.opname in (FORWARD_CONDITIONAL_JUMP_OPS | SHORT_CIRCUIT_JUMP_OPS)
                        and ('IF_TRUE' in _main_cond_last.opname
                             or 'IF_FALSE' in _main_cond_last.opname
                             or 'IF_NONE' in _main_cond_last.opname)
                        and _main_cond_last.argval is not None):'''

    # ---------------- Edit B ----------------
    b_anchor = span(lines, 2258, 2267,
                    '        def _is_normal_flow_sink(block):\n'
                    '            if not _normal_successors(block):\n'
                    '                return True\n'
                    '            _last = block.get_last_instruction()\n'
                    "            if _last and _last.opname in ('RETURN_VALUE', 'RETURN_CONST', 'RAISE_VARARGS', 'RERAISE'):\n"
                    '                return True\n'
                    '            return False\n'
                    '\n'
                    '        _then_is_sink = _is_normal_flow_sink(then_succ)\n'
                    '        _else_is_sink = _is_normal_flow_sink(else_succ)')
    b_repl = '''        def _is_normal_flow_sink_single(block):
            # [R75-FIX3-B0] 经典单块判据原样保留：它是下方冲突门的基线与回退目标。
            if not _normal_successors(block):
                return True
            _last = block.get_last_instruction()
            if _last and _last.opname in ('RETURN_VALUE', 'RETURN_CONST', 'RAISE_VARARGS', 'RERAISE'):
                return True
            return False

        def _is_normal_flow_sink(block):
            # [R75-FIX3-B] 链式闭合死端 sink（对「纯 sink 分支」原则的一次结构性放宽）。
            # 根因：分支入口块常以 LOAD_GLOBAL/LOAD_CONST/条件跳开头，真终态块在其后继里，
            #   单块判据判否 → 本方法「某分支是纯 sink 时 merge 取对侧分支的 JUMP_FORWARD
            #   目标」的 sink 侧规则不触发 → merge 落回 else 入口而非对侧臂出口，then 臂
            #   越过真实 merge 无界吸收共享尾：real_quote.get_real_minute_kline 的 else 臂
            #   （入口 358 LOAD_GLOBAL、370 RETURN_VALUE）、get_tick_direction 的 else 臂
            #   （入口 944 条件链、1102 RETURN_VALUE）即此形态。
            # 同层身份判据：从入口沿正常后继（排除异常边）取可达子图；子图内除入口外每块
            #   的 predecessors 全落在子图内（闭合：不与任何外部控制流汇合，即该臂不会
            #   落入任何 merge），且子图内存在 RETURN/RAISE 终态出口。闭合死端永远不是
            #   merge，故该臂等效纯 sink；入口自身的外部前驱不参与判据（分支入口本就来自
            #   上层条件）。只读后继边、predecessors 与 opcode，不读名字/常量/偏移阈值/
            #   函数名/新 self 状态；子图上限 64 块，超限按原单块判据处理。
            # 去向与守卫：返回值只在下方「冲突受限升级」门内参与 _then_is_sink /
            #   _else_is_sink 两个 sink 侧 merge 规则（与本方法 docstring 的纯 sink 分支
            #   原则一致），不改其它规则；闭合或终态判否即逐位维持原单块行为。
            if not _normal_successors(block):
                return True
            _last = block.get_last_instruction()
            if _last and _last.opname in ('RETURN_VALUE', 'RETURN_CONST', 'RAISE_VARARGS', 'RERAISE'):
                return True
            _seen = {block}
            _work = [block]
            while _work and len(_seen) <= 64:
                _cur = _work.pop()
                for _nx in _normal_successors(_cur):
                    if _nx not in _seen:
                        _seen.add(_nx)
                        _work.append(_nx)
            if len(_seen) > 64:
                return False
            for _b in _seen:
                if _b is block:
                    continue
                for _p in (getattr(_b, 'predecessors', None) or ()):
                    if _p not in _seen:
                        return False
            for _b in _seen:
                _bl = _b.get_last_instruction()
                if not _normal_successors(_b):
                    return True
                if _bl and _bl.opname in ('RETURN_VALUE', 'RETURN_CONST',
                                          'RAISE_VARARGS', 'RERAISE'):
                    return True
            return False

        # [R75-FIX3-B·门] 冲突受限升级。
        # 根因：经典单块判据已把某一侧判成 sink 时（如 quotation.change_his_to_forward
        #   的 `else: return data` 单块 return 早就是 sink），闭合扩展会把对侧「含共享尾
        #   的闭合死端」也判成 sink；下方两条 sink 侧规则的前提是恰一侧为 sink
        #   （`_else_is_sink and not _then_is_sink` / `_then_is_sink and not _else_is_sink`），
        #   双 sink 让两条规则同时失效，merge 落到其后的普通规则，then 臂反向吞掉本该
        #   外置的共享尾（字节码少一条跳转，decomp 指令数 −1）。
        # 同层身份判据：只读两侧分支入口块的单块判据布尔值与闭合子图布尔值，不读块偏移、
        #   名字、常量、函数名、新 self 状态。
        # 去向与守卫：仅当两侧单块判据都为 False（经典判据对两侧都无结论，正是闭合扩展
        #   要补的盲区）才启用闭合扩展；扩展后两侧同真（退化双 sink）整体回退单块判据，
        #   恢复互斥前提；任一侧单块判据已为 True 时逐位沿用单块判据，零行为变化。
        _then_is_sink_single = _is_normal_flow_sink_single(then_succ)
        _else_is_sink_single = _is_normal_flow_sink_single(else_succ)
        if not _then_is_sink_single and not _else_is_sink_single:
            _then_is_sink = _is_normal_flow_sink(then_succ)
            _else_is_sink = _is_normal_flow_sink(else_succ)
            if _then_is_sink and _else_is_sink:
                _then_is_sink = _then_is_sink_single
                _else_is_sink = _else_is_sink_single
        else:
            _then_is_sink = _then_is_sink_single
            _else_is_sink = _else_is_sink_single'''

    # ---------------- Edit B2 ----------------
    c_anchor = span(lines, 17664, 17669,
                    '                            _if_struct_blocks = ({block, then_succ, else_succ,\n'
                    '                                                 _else_succ_original} | chain_blocks)\n'
                    '                            _else_has_external_pred = any(\n'
                    '                                p not in _if_struct_blocks\n'
                    '                                for p in else_succ.predecessors\n'
                    '                            )')
    c_repl = '''                            # [R75-FIX3-B2] 外部前驱区分「顺序落入」与「条件跳入」。
                            # 根因：以条件跳转目标身份进入 else_succ 的前驱 P（P 末条为前向
                            #   条件跳且跳转目标就是 else_succ 块首）说明 else_succ 是另一条
                            #   条件的共享假边入口（前一条件的假边与本条件的假边落进同一
                            #   else 体），不是「本 if 之后的顺序续行点」。原判据把这类共享
                            #   入口当 post-if 点 → merge := else_succ → else_blocks 归空、
                            #   then 臂越过真实 merge 无界吸收（real_quote.get_real_minute_kline
                            #   的 `len(redata)>0 and flag==0` 共用 else 即此形态）。
                            # 同层身份判据：只读前驱末条指令的 opcode（前向条件跳）与其跳转
                            #   目标是否等于 else_succ.start_offset，以及前驱是否属于当前 if
                            #   结构块集（block/then_succ/else_succ/_else_succ_original/chain）
                            #   的成员身份；不读名字/常量/偏移阈值/函数名/新 self 状态。
                            # 去向与守卫：条件跳入的外部前驱 continue 跳过，只有真正的顺序
                            #   落入才置 _else_has_external_pred=True 进入原
                            #   _r49a → merge=else_succ 分支；否则保持 merge=None 继续走
                            #   _compute_merge_from_jump_targets。
                            _if_struct_blocks = ({block, then_succ, else_succ,
                                                 _else_succ_original} | chain_blocks)
                            _else_has_external_pred = False
                            for p in else_succ.predecessors:
                                if p in _if_struct_blocks:
                                    continue
                                _pli = p.get_last_instruction()
                                if (_pli is not None
                                        and _pli.opname in (FORWARD_CONDITIONAL_JUMP_OPS | SHORT_CIRCUIT_JUMP_OPS)
                                        and _pli.argval is not None
                                        and _pli.argval == else_succ.start_offset):
                                    continue
                                _else_has_external_pred = True
                                break'''

    # ---------------- Edit D ----------------
    d_anchor = span(lines, 19963, 19963,
                    '        if merge is None and then_blocks and elif_info.get("final_else"):')
    d_repl = '''        # [R75-FIX3-D] 平坦 elif 链判否（臂出口落到终态块且 ≠ 调用方 merge）。
        # 根因：调用方已给出非空 merge 时，若链内某臂的出口落到一个终态块（RETURN/RAISE）
        #   而该终态块不是 merge，这条链就不能渲染成同层 if/elif 序列——平坦渲染会让各臂
        #   JUMP 到 merge，绕过位于臂出口与 merge 之间的终态语句，字节码分叉
        #   （real_quote.get_tick_direction 即此形态：then 臂跳 1106、else 内 flag 链各臂
        #   汇入 1102 `return redata` 终态，真共享 merge 是 1106；采纳 1102 为链 merge 会让
        #   then 臂越过 `return redata` 吸收整条共享尾，含其后的 try 区）。
        # 同层身份判据：只读臂块的 successors（排除异常边）、臂块与后继块末条指令的 opcode
        #   是否终态、以及调用方 merge 的块身份；不读名字/常量/偏移阈值/函数名/新 self
        #   状态/跨层 region.entry 引用。
        # 去向与守卫：命中即 return None，调用方回落 _build_basic_if_region，用同一
        #   then/else/merge 构建 IF_THEN_ELSE 嵌套形态（else 臂内递归重建 flag 链），本
        #   方法此前对 elif_info/else_blocks 的改写随之丢弃；merge 为 None 或不命中则
        #   原样继续原链路（零行为变化）。
        if merge is not None:
            _flat_reject = False
            _flat_arms = list(then_blocks)
            for _flat_body in (elif_info.get("bodies") or []):
                _flat_arms.extend(_flat_body)
            for _flat_b in _flat_arms:
                _flat_bl = _flat_b.get_last_instruction()
                if (_flat_bl is None
                        or _flat_bl.opname in ('RETURN_VALUE', 'RETURN_CONST',
                                               'RAISE_VARARGS', 'RERAISE')):
                    continue
                _flat_exc = getattr(_flat_b, 'exception_successors', None) or set()
                for _flat_s in list(_flat_b.successors):
                    if _flat_s in _flat_exc:
                        continue
                    if _flat_s.start_offset == merge.start_offset:
                        continue
                    _flat_sl = _flat_s.get_last_instruction()
                    if (_flat_sl is not None
                            and _flat_sl.opname in ('RETURN_VALUE', 'RETURN_CONST',
                                                    'RAISE_VARARGS', 'RERAISE')):
                        _flat_reject = True
                        break
                if _flat_reject:
                    break
            if _flat_reject:
                return None
        if merge is None and then_blocks and elif_info.get("final_else"):'''

    # ---------------- Edit E ----------------
    e_anchor = span(lines, 18152, 18152,
                    '            # 如果检测到链式比较，设置链式比较信息到区域上')
    e_repl = '''            if (region is not None
                    and _main_inline_boolop_chain is not None
                    and _main_inline_boolop_chain.get('op') == 'or'):
                # [R75-FIX3-E] or 链成员条件区摘除（兄弟区抢发导致 else 臂整段丢失）。
                # 根因：_identify_conditional_regions 按反向偏移处理块，成员条件块（偏移更大）
                #   先各自建成一个 IfRegion（entry=成员块，携带 else 臂其余全部代码）；随后链首
                #   块折出 or 链 IfRegion（entry=链首，blocks 含全部链成员）。生成阶段按偏移升序
                #   先发射链首 region 并把成员块标为 generated，成员 region 命中 entry-in-
                #   generated 早退返回 []，其 else 臂（循环/内部 if/后续语句）整段静默丢失
                #   （real_quote.get_real_minute_kline_bk 的 `if fq is None or ex_info is None:`
                #   即此形态：产物只剩 `return kline`，函数后半被整体截断、字节码骤减）。
                # 同层身份判据：只读本 or 链的成员块集合、候选区的区域类型（IF_ELIF_CHAIN 不动，
                #   避免拆掉真 elif 归约）与 entry 块身份（entry 必须正是链成员且非链首块）；不读
                #   名字/常量/偏移阈值/函数名/新 self 状态/跨层 region.entry 引用。
                # 去向与守卫：命中即从 if_regions 摘除该成员区并清掉其父挂接；其 blocks 中不被
                #   链区、本方法可见的其它区域（loop/try/with/match/boolop/ternary/assert 及其余
                #   if）占有的块，逐块补成 BASIC 区域顶上（与生成器既有 orphan→BASIC 兜底同
                #   规则），确保 else 臂语句按偏移顺序在链区之后发射；块已有归属则不动。仅 or
                #   链命中才执行，and 链与无链路径零行为变化。
                _e_members = set(_main_inline_boolop_chain.get('blocks', []))
                _e_taken = set(region.blocks)
                for _e_v in list(if_regions):
                    if not isinstance(_e_v, IfRegion):
                        continue
                    if _e_v.region_type == RegionType.IF_ELIF_CHAIN:
                        continue
                    if (_e_v.entry is None or _e_v.entry is block
                            or _e_v.entry not in _e_members):
                        continue
                    _e_rest = set(_e_v.blocks) - _e_taken
                    for _e_owner in (loop_regions, assert_regions, try_regions,
                                     with_regions, match_regions, boolop_regions,
                                     ternary_regions, if_regions):
                        for _e_or in _e_owner:
                            if _e_or is _e_v or _e_or is region:
                                continue
                            _e_rest -= _e_or.blocks
                    if_regions.remove(_e_v)
                    _e_vp = getattr(_e_v, 'parent', None)
                    if _e_vp is not None and hasattr(_e_vp, 'children'):
                        try:
                            _e_vp.children.remove(_e_v)
                        except ValueError:
                            pass
                    _e_v.parent = None
                    for _e_b in sorted(_e_rest, key=lambda x: x.start_offset):
                        if_regions.append(Region(region_type=RegionType.BASIC,
                                                 entry=_e_b, blocks={_e_b}))
            # 如果检测到链式比较，设置链式比较信息到区域上'''

    # ---------------- Edit F ----------------
    f_anchor = span(lines, 17704, 17721,
                    '            if (merge is None and _main_inline_boolop_chain is not None):\n'
                    '                # [R35 fix] else_succ 是条件块（潜在 elif 条件）时跳过，交给 elif 链检测。\n'
                    '                # 当 and/or 短路链的 then body 以 return/sink 终止，NCPD=None 且\n'
                    '                # _compute_merge_from_jump_targets=None，此兜底会设 merge=else_succ。\n'
                    '                # 若 else_succ 是 elif 条件块，merge=else_succ 使 else_blocks 为空\n'
                    '                #（entry==merge），阻止 IF_ELIF_CHAIN 创建，elif 被独立识别为 IF_THEN。\n'
                    '                # 典型场景（handlers._target）：\n'
                    '                #   if A and B:       # and 链，then body 含 while+return None (sink)\n'
                    '                #       ...\n'
                    '                #   elif C:           # else_succ=408 是 elif 条件块\n'
                    '                #       ...\n'
                    '                #   elif D: ...\n'
                    '                # 原逻辑设 merge=408，else_blocks=[]，IF_ELIF_CHAIN 无法创建。\n'
                    '                _r49a_tail = self._r49a_shared_sink_tail_merge(\n'
                    '                    block, then_succ, else_succ,\n'
                    '                    {block, then_succ, else_succ} | chain_blocks)\n'
                    '                merge = (_r49a_tail if _r49a_tail is not None\n'
                    '                         else else_succ)')
    f_repl = '''            if (merge is None and _main_inline_boolop_chain is not None):
                # [R35 fix] else_succ 是条件块（潜在 elif 条件）时跳过，交给 elif 链检测。
                # 当 and/or 短路链的 then body 以 return/sink 终止，NCPD=None 且
                # _compute_merge_from_jump_targets=None，此兜底会设 merge=else_succ。
                # 若 else_succ 是 elif 条件块，merge=else_succ 使 else_blocks 为空
                #（entry==merge），阻止 IF_ELIF_CHAIN 创建，elif 被独立识别为 IF_THEN。
                # 典型场景（handlers._target）：
                #   if A and B:       # and 链，then body 含 while+return None (sink)
                #       ...
                #   elif C:           # else_succ=408 是 elif 条件块
                #       ...
                #   elif D: ...
                # 原逻辑设 merge=408，else_blocks=[]，IF_ELIF_CHAIN 无法创建。
                # [R75-FIX3-F] else_succ 是本 if 自身的终点臂时，不再把 merge 落到它身上。
                # 根因：or 链的 else 臂以 RETURN/RAISE 终止（无正常后继）时，then/else 两臂
                #   都到不了任何汇合点——merge 根本不存在。此时 merge:=else_succ 会让
                #   else_blocks 归空（entry==merge），链区退化成 IF_THEN；其 else 臂的块
                #   （else_succ 自身）既不在链区 blocks、也不在父 elif 链的 then/else/elif
                #   body 列表里，生成时无人发射，只能掉到函数末尾的孤儿兜底补发
                #   （wizard_quant_api.filter_desicion 的 `return up_v_desicion(...)`
                #   被挪到整条 if-elif 链之后、字节码序列缺 3 条即此形态）。
                # 同层身份判据：只读 else_succ 的正常后继集合（排除异常边）与末条指令
                #   opcode 是否 RETURN/RAISE/RERAISE 终态；不读名字/常量/偏移阈值/
                #   函数名/文件名/_self 状态。
                # 去向与守卫：else_succ 是终点臂时整个兜底跳过（merge 保持 None，下方按
                #   merge=None 分别收集 then/else 两臂，_build_elif_region 出
                #   IF_THEN_ELSE，else 臂随链区一起发射）；else_succ 不是终点（Round33
                #   原场景：then 体可跌落到共享续行点）时逐位维持原逻辑（_r49a → else_succ）。
                #   [收窄] 仅 op=='or' 链才跳过此兜底：and 链的同层场景（load_daily.
                #   api_get_from_zeromq 的 `message and len(...)`）中 else_succ 是共享尾部，
                #   merge=else_succ 是正确汇合点；若跳过则 merge=None，嵌套 try 的
                #   gap 块触发 R71 吞并丢 `return (None, -1)`（例外边）。
                _f_else_last = else_succ.get_last_instruction()
                _f_else_exc = getattr(else_succ, 'exception_successors', None) or set()
                _f_else_is_sink = (
                    not [s for s in else_succ.successors if s not in _f_else_exc]
                    or (_f_else_last is not None
                        and _f_else_last.opname in ('RETURN_VALUE', 'RETURN_CONST',
                                                    'RAISE_VARARGS', 'RERAISE')))
                #   [收窄-2] 再加 then 臂无正常后继（终点臂）：若 then 可达到共享续行点
                #   （Round33 原场景 time_validator.can_cancel_order 的 then→else 可达），
                #   merge=else_succ 是正确汇合点，跳过会改变区域形态（history_data_source.
                #   get_price 15/18、custom_tools 5/6 即此类）；两臂终点时才是独立终点臂。
                #   [收窄-3] 再加“本块有条件跳转前驱”：顶层 if（块 0 = 函数入口、无前驱或仅语句前驱）
                #   的同层场景中 else 臂就是正确的后续语句（risk_calculation.next_day
                #   的 `if not A or B:`），merge=else_succ 直接正确；嵌套在外层条件臂内的
                #   链成员才会被链区排除、落到函数末尾孤儿兜底错位（wizard 即此类）。
                _f_then_last = then_succ.get_last_instruction() if then_succ else None
                _f_then_exc = getattr(then_succ, 'exception_successors', None) or set()
                _f_then_terminal = (
                    then_succ is not None
                    and not [s for s in then_succ.successors if s not in _f_then_exc])
                #   [收窄-4] 再加“祖先链上溯存在链证据”：沿前驱回溯找到某个条件块
                #   的其他后继也是条件块（elif 链续接）才认定本 if 嵌在多臂链内。
                #   单局外层 if/else（其他后继是 RETURN，无链续接也无祖先链证据，如
                #   同层 `if not A or B: return 1 else: return 2` 独立形态）中
                #   merge=else_succ 本就正确；只有链成员的 else 臂才会被链区排除。
                _f_cond_pred = any(
                    p.get_last_instruction() is not None
                    and ('IF_' in p.get_last_instruction().opname)
                    for p in (block.predecessors or []))
                _f_outer_chain = False
                _f_seen = set()
                _f_stack = list(block.predecessors or [])
                while _f_stack and not _f_outer_chain:
                    _fp = _f_stack.pop()
                    if id(_fp) in _f_seen:
                        continue
                    _f_seen.add(id(_fp))
                    _fl = _fp.get_last_instruction()
                    if _fl is not None and 'IF_' in _fl.opname:
                        for _fs in (_fp.successors or []):
                            if _fs is block:
                                continue
                            _fsl = _fs.get_last_instruction()
                            if _fsl is not None and 'IF_' in _fsl.opname:
                                _f_outer_chain = True
                                break
                    if not _f_outer_chain:
                        _f_stack.extend(_fp.predecessors or [])
                if not (_f_else_is_sink and _f_then_terminal and _f_cond_pred
                        and _f_outer_chain
                        and ((_main_inline_boolop_chain or {}).get('op') == 'or')):
                    _r49a_tail = self._r49a_shared_sink_tail_merge(
                        block, then_succ, else_succ,
                        {block, then_succ, else_succ} | chain_blocks)
                    merge = (_r49a_tail if _r49a_tail is not None
                             else else_succ)'''

    edits = {'or1': (a_anchor, a_repl),
             'sink1': (b_anchor, b_repl),
             'xp1': (c_anchor, c_repl),
             'chf1': (d_anchor, d_repl),
             'e1': (e_anchor, e_repl),
             'f1': (f_anchor, f_repl)}
    for name, (anchor, repl) in edits.items():
        n = src.count(anchor)
        assert n == 1, '%s anchor count=%d' % (name, n)
        assert repl != anchor
        assert all(k in repl for k in ('根因', '同层身份判据', '去向与守卫')), name
        p = '%s/%s.json' % (OUT, name)
        json.dump({'file': REL, 'edits': [{'anchor': anchor, 'repl': repl}]},
                  io.open(p, 'w', encoding='utf-8', newline='\n'),
                  ensure_ascii=False, indent=1)
        print('wrote', p)

    combo = {'file': REL,
             'edits': [{'anchor': a_anchor, 'repl': a_repl},
                       {'anchor': b_anchor, 'repl': b_repl},
                       {'anchor': d_anchor, 'repl': d_repl},
                       {'anchor': e_anchor, 'repl': e_repl},
                       {'anchor': f_anchor, 'repl': f_repl}]}
    p = '%s/trym.json' % OUT
    json.dump(combo, io.open(p, 'w', encoding='utf-8', newline='\n'),
              ensure_ascii=False, indent=1)
    print('wrote', p)
    print('anchors ok (all count==1, 三要素 present)')


if __name__ == '__main__':
    main()
