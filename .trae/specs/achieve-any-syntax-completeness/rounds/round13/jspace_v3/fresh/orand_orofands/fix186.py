# -*- coding: utf-8 -*-
"""rr-v5r186 patch: or-of-ands 三元条件链补全族（TernaryRegion 链补全 + BoolOp 前缀溶解 + import 前缀去重）。

用法（cwd 任意；默认仓库根 F:\\Downloads\\pythoncdc-main）:
    D:/Python/python.exe -I -X utf8 fix186.py            # 应用补丁（幂等）
    D:/Python/python.exe -I -X utf8 fix186.py --revert   # 回退（往返 sha 一致）

约束（rules.md）:
  §1.4 I.4 白名单：新增判据只读 CFG 块末 opcode 族 / 条件后继集合 / 后继汇聚关系 /
        区域身份（entry 相等、块集包含）/ 既有发射状态；不读文件名、函数名、偏移阈值。
  §2.1：新增符号 `_ternary_chain_completion`、`_ofc_*` 均无禁用前缀。
  §2.2：无硬编码深度/计数上限；链收集的终止性由 visited 块集有限性保证。
  编码：两文件均为 UTF-8 BOM 单头（efbbbf），补丁保持不剥 BOM。
  锚点：每个 hunk 的 old 文本在目标文件中必须恰好出现 1 次（count==1）。
"""
from __future__ import annotations

import hashlib
import io
import os
import py_compile
import sys

REPO = os.environ.get('R186_REPO') or r'F:\Downloads\pythoncdc-main'
RAG = os.path.join(REPO, 'core', 'cfg', 'region_analyzer.py')
RAG2 = os.path.join(REPO, 'core', 'cfg', 'region_ast_generator.py')

# ---------------------------------------------------------------- hunk 1
# region_analyzer.py：新增 `_ternary_chain_completion` 判据（插在 `_is_ternary_block` 之前）
H1_OLD = '''        def _is_ternary_block(block):
            succs = list(block.conditional_successors)
'''

H1_NEW = '''        def _ternary_chain_completion(block):
            """条件链补全判据（混合短路 or-of-ands 的「双条件后继」形态）。

            ①算法依据：No More Gotos 章节「区域归约算法四原则」（自底向上归约 /
              每块唯一归属 / 嵌套即抽象节点 / 父引用子入口）。CPython 对混合短路
              条件 `(A and B) or (C and D)` 的 lowering 使**头块的两条出边都落在
              条件链成员块**上（A 的假边 = or 下一操作数 C 的测试块，B 的真边 =
              三元真值块），两条出边都不是值块。既有
              `_build_ternary_condition_chain` 只沿「与 initial_jt 共享假出口」的
              均匀链前进，在 and→or 边界处止步（B 的真跳转目标不是假值块），把
              or 段（C and D）留在链外；随后真/假值块校验读到的是条件成员块，
              值块守卫拒绝 ⇒ TernaryRegion 缺席，IfRegion 把残局物化成
              `if not (A and B):` 并把后续语句吞进 then 体。
            ②归约顺序：自底向上——内层条件成员块先按块收集，本判据只产出
              「链块序 + 真/假值块」三元组，随后仍走既有 `len(chain) > 1` 路径的
              全部守卫（单表达式值块 / return-body / CALL 丢弃 / 共享 merge）逐条
              复核，本判据不跳过任何既有门。
            ③唯一归属判定（全部同层块结构事实，C1）：头块末指令为正向条件跳转，
              且其**两条**条件后继都是条件链成员（末指令为正向条件跳转、恰有两条
              条件后继）；沿两条出边按 visited 块集遍历（终止性由块集有限性保证，
              不设深度/计数上限），仍为链成员的块收进链、其余记为出口候选；出口
              候选须恰为两个互异块并逐块通过 `_ofc_value_block`（单表达式块 ∧ 无
              POP_TOP ∧ 非 RETURN 收尾）；两出口的正常后继须汇聚同一块（值菱形，
              由 `_is_single_expression_block` 的值语义所要求）。链中恰有一个成员
              （判定成员）的两条条件后继就是这两个出口，且它须为块序末位（前向跳转
              链的求值顺序末项）；真/假取值沿用既有链尾约定（非跳转目标 = 真值块）。
              最后按各成员末跳转 opcode 族做极性文法守卫：首成员须为 IF_FALSE 族
              （and 短路）、且无 or 后紧跟 or——即 only `and+ (or and+)*`，正是生成端
              or_groups 分组能正确重建的族；or→and 镜像族与取反族（`not (…)`）不在
              本族，维持既有拒绝路径（逐字节不变）。
            ④嵌套处理：命中的链块整体归 TernaryRegion（每块唯一归属）；值块若已是
              内层三元入口，按既有 nested_ternary_regions 通道作为抽象节点被父区域
              引用，本判据不展开子区域内部（C2）。
            ⑤入口引用语义：返回 (chain_blocks, true_block, false_block)，链首恒为
              入参 block 自身（父区域以该入口引用整条条件链）；返回 None = 未命中，
              调用方逐位维持原拒绝行为。
            ⑥反编译流程：`_detect_ternary_pattern` 内、[B6-ternary] 与 [TCX-扩展]
              续接通道之后的条件链补全通道；命中后仍由既有 TernaryRegion 创建路径
              与生成端 `_build_ternary_boolop_condition`（按各成员末跳转极性推导
              and/or 分组）重建条件。
            C 条款：[C1] 只读同层块末 opcode 族 / 条件后继集合 / 后继汇聚关系；
            [C2] 值块经既有 `_is_single_expression_block` 黑箱校验，不窥视子区域；
            [C3] 未命中或任一校验不成立即返回 None，调用方保持原路径逐字节不变。
            """
            last = block.get_last_instruction()
            if (last is None
                    or last.opname not in FORWARD_CONDITIONAL_JUMP_OPS
                    or not isinstance(getattr(last, 'argval', None), int)):
                return None
            heads = sorted(block.conditional_successors,
                           key=lambda s: s.start_offset)
            if len(heads) != 2:
                return None

            def _is_chain_member(b):
                bl = b.get_last_instruction()
                return bool(bl is not None
                            and bl.opname in FORWARD_CONDITIONAL_JUMP_OPS
                            and isinstance(getattr(bl, 'argval', None), int)
                            and len(b.conditional_successors) == 2)

            # 双条件后继：头块两条出边都是条件链成员（无一到达值块）。
            if not (_is_chain_member(heads[0]) and _is_chain_member(heads[1])):
                return None

            def _ofc_value_block(b):
                eff = [i for i in b.instructions if i.opname not in NOISE_OPS]
                if not eff:
                    return False
                if eff[-1].opname in ('RETURN_VALUE', 'RETURN_CONST'):
                    return False
                if any(i.opname == 'POP_TOP' for i in eff):
                    return False
                return self._is_single_expression_block(b)

            chain = [block]
            seen = {id(block)}
            pending = list(heads)
            terminals = []
            while pending:
                cur = pending.pop(0)
                if id(cur) in seen:
                    continue
                seen.add(id(cur))
                if _is_chain_member(cur):
                    chain.append(cur)
                    pending.extend(cur.conditional_successors)
                else:
                    terminals.append(cur)
            if len(terminals) != 2 or terminals[0] is terminals[1]:
                return None
            if not (_ofc_value_block(terminals[0])
                    and _ofc_value_block(terminals[1])):
                return None
            _term_set = set(terminals)
            deciders = [c for c in chain
                        if set(c.conditional_successors) == _term_set]
            if len(deciders) != 1:
                return None
            decider = deciders[0]
            decider_last = decider.get_last_instruction()
            if decider_last is None or decider_last.argval is None:
                return None
            true_block = next((s for s in decider.conditional_successors
                               if s.start_offset != decider_last.argval), None)
            false_block = next((s for s in decider.conditional_successors
                                if s.start_offset == decider_last.argval), None)
            if true_block is None or false_block is None:
                return None
            if not (_ofc_value_block(true_block) and _ofc_value_block(false_block)):
                return None

            def _ofc_normal_succs(b):
                exc = set(getattr(b, 'exception_successors', None) or ())
                return [s for s in b.successors if s not in exc]

            true_succs = _ofc_normal_succs(true_block)
            false_succs = _ofc_normal_succs(false_block)
            if (len(true_succs) != 1 or len(false_succs) != 1
                    or true_succs[0] is not false_succs[0]):
                return None
            chain_sorted = sorted(chain, key=lambda b: b.start_offset)
            if chain_sorted[-1] is not decider:
                return None
            # 极性文法守卫（C1：只读各成员末跳转 opcode 族）：生成端
            # `_build_ternary_boolop_condition` 的 or_groups 分组只对
            # 「and 段由单个 or 连接」（and+ (or and+)*）这一族条件成立。
            # 首成员须为 IF_FALSE 族（and 短路），且不得出现 or 后紧跟 or——
            # 否则是 or→and 镜像族 / 取反族（`x if (a or b) and (c or d)`、
            # `x if not (…)`），其重建规则不属本族，保持既有拒绝路径
            # （逐字节不变，C3）。
            _ops = []
            for _m in chain_sorted:
                _ml = _m.get_last_instruction()
                if _ml is None:
                    return None
                _ops.append('or' if 'TRUE' in _ml.opname else 'and')
            if _ops[0] != 'and':
                return None
            for _k in range(len(_ops)):
                if _ops[_k] != 'or':
                    continue
                if _k + 1 >= len(_ops) or _ops[_k + 1] != 'and':
                    return None
            return chain_sorted, true_block, false_block

        def _is_ternary_block(block):
            succs = list(block.conditional_successors)
'''

# ---------------------------------------------------------------- hunk 2
# region_analyzer.py：`_can_be_ternary_header` 对「被截断 BoolOp 前缀」放行
H2_OLD = '''            existing = self.block_to_region[block]
            return existing.can_be_ternary_header(block, self)
'''

H2_NEW = '''            existing = self.block_to_region[block]
            if existing.can_be_ternary_header(block, self):
                return True
            # [r186-OROFANDS-cpl] 既有 BoolOpRegion 是**被截断的条件链前缀**时的
            # 放行通道。识别条件（同层块结构事实 + 区域身份）：占用块的是以
            # 本块为 entry 的 BoolOpRegion（其 op_chain 只覆盖混合短路条件的前
            # 缀段，or 段因 and→or 边界留在链外），且本块满足
            # `_ternary_chain_completion`「双条件后继 + 值菱形出口」判据。
            # 归约方式：放行 TernaryRegion 由补全链整体认领这些块（每块唯一归属
            # ——BoolOpRegion 的 op_chain 全部包含于补全链，创建端 skip_ternary
            # 的 chain_only_in_candidate 分支据此放行升级）；op 极性由生成端按
            # 各成员末跳转方向重导，不用被截断的 op_chain。不命中即维持原
            # `existing.can_be_ternary_header` 拒绝，逐字节不变（C3）。
            if (isinstance(existing, BoolOpRegion)
                    and existing.entry is block
                    and _ternary_chain_completion(block) is not None):
                return True
            return False
'''

# ---------------------------------------------------------------- hunk 3
# region_analyzer.py：`_detect_ternary_pattern` 内的链补全通道（TCX 之后）
H3_OLD = '''                            chain_blocks = list(chain_blocks) + [b for b, _ in _tcx_r.op_chain]
                            _tcx_boolop_extended = True
'''

H3_NEW = '''                            chain_blocks = list(chain_blocks) + [b for b, _ in _tcx_r.op_chain]
                            _tcx_boolop_extended = True

            # [r186-OROFANDS-cpl] 混合短路 or-of-ands 的链尾续接通道。
            # 识别条件（全部同层块结构事实，C1）：TCX 续接未命中；头块满足
            # `_ternary_chain_completion` 的「双条件后继 + 唯一判定成员 + 值菱形
            # 出口」判据，且其补全链是当前链的严格超集（当前链块全部落在补全链
            # 内）。`x if (A and B) or (C and D) else y`：既有条件链 walk 在
            # and→or 边界止步于 B（链 = [A, B]），补全链 = [A, B, C, D]，真/假
            # 值块由判定成员 D 的两条出边给出。
            # 归约方式（C2 黑箱组合）：chain_blocks 升级为补全链，真/假值块同步
            # 换为值菱形出口；随后走既有 `len(chain) > 1` 路径的全部守卫与
            # TernaryRegion 创建（链首仍为本块入口）。op 极性不由被截断的
            # BoolOpRegion.op_chain 提供（下方 boolop_op_chain 升级对本通道禁用），
            # 由生成端按各成员末跳转方向推导混合 and/or 分组。
            # AST 映射：ast.IfExp(test=BoolOp(or, [BoolOp(and,[A,B]),
            # BoolOp(and,[C,D])]), body=<真值块>, orelse=<假值块>)。
            # 未命中（链非超集 / 判据不成立）⇒ 逐位维持原路径（C3）。
            _ofc_completed = False
            if not _tcx_boolop_extended:
                _ofc_result = _ternary_chain_completion(block)
                if _ofc_result is not None:
                    _ofc_chain, _ofc_true, _ofc_false = _ofc_result
                    _ofc_ids = {id(_ofc_b) for _ofc_b in _ofc_chain}
                    _ofc_cur = list(chain_blocks or [])
                    if (all(id(_ofc_b) in _ofc_ids for _ofc_b in _ofc_cur)
                            and len(_ofc_chain) > len(_ofc_cur)):
                        chain_blocks = _ofc_chain
                        true_block = _ofc_true
                        false_block = _ofc_false
                        _ofc_completed = True
'''

# ---------------------------------------------------------------- hunk 4
# region_analyzer.py：补全通道禁用被截断 op_chain 的替换
H4_OLD = '''            # 如果有 BoolOp op_chain，将其转换为 condition_chain_blocks 格式
            if boolop_op_chain and len(chain_blocks) > 1:
                chain_blocks = list(boolop_op_chain)  # 现在是 [(block, op), ...] 格式
'''

H4_NEW = '''            # 如果有 BoolOp op_chain，将其转换为 condition_chain_blocks 格式
            # [r186-OROFANDS-cpl] 仅当该 op_chain **完整覆盖**条件链时才是同一
            # 条链的操作符标注；[r186-OROFANDS-cpl] 补全通道下 op_chain 只是被
            # 截断的前缀段，用它替换会丢掉 or 段成员（条件退化）。此时保留纯块
            # 链，交生成端按各成员末跳转极性推导（C1：链块集合与 op_chain 块集合
            # 的包含关系是区域身份事实，无名字/偏移特判）。
            if boolop_op_chain and len(chain_blocks) > 1 and not _ofc_completed:
                chain_blocks = list(boolop_op_chain)  # 现在是 [(block, op), ...] 格式
'''

# ---------------------------------------------------------------- hunk 5
# region_analyzer.py：被三元整块吞并的 BoolOpRegion 同步从识别结果列表摘除
H5_OLD = '''            for r in to_remove:
                self.regions.remove(r)
                for b in r.blocks:
                    if b in self.block_to_region and self.block_to_region[b] is r:
                        del self.block_to_region[b]
'''

H5_NEW = '''            for r in to_remove:
                self.regions.remove(r)
                for b in r.blocks:
                    if b in self.block_to_region and self.block_to_region[b] is r:
                        del self.block_to_region[b]
                # [r186-OROFANDS-cpl] 被本三元**整块吞并**的 BoolOpRegion 同步从
                # Phase 2 识别结果列表摘除。判据（区域身份 + 块集严格包含，C1）：
                # BoolOpRegion 且 entry 与本三元 entry 同块（同一条件头）且其
                # op_chain 块集是本三元条件链块集的**真子集**——该 BoolOp 只是被
                # 补全的条件链前缀段，不是独立表达式结构。只摘 self.regions 会让
                # 它经 analyze() 的 filtered_boolop_regions 重新进入 all_regions，
                # 生成端把同一条件头的已完结前导语句（如模块 import/赋值）再发
                # 一遍（重复行）。严格包含不可放宽：BoolOp 链与该三元链同集时
                # （值是纯 BoolOp、三元是重复识别，如 `file and 'I' or 'D'`），
                # BoolOp 才是逐字节正确的载体，必须保留其优先级。未命中（非
                # BoolOp / 不同入口 / 非真子集）⇒ 行为与既有 to_remove 一致，
                # 逐字节不变（C3）。
                if (isinstance(r, BoolOpRegion)
                        and r.entry is region.entry
                        and r.blocks and set(r.blocks) <= set(region.blocks)):
                    _ofc_op_ids = {id(_ob) for _ob, _ in (r.op_chain or [])}
                    _ofc_chain_ids = {
                        id(_cb[0] if isinstance(_cb, tuple) else _cb)
                        for _cb in (region.condition_chain_blocks or [])}
                    if (_ofc_op_ids
                            and _ofc_op_ids < _ofc_chain_ids):
                        for _bl in (boolop_regions, conditional_regions):
                            if r in _bl:
                                _bl.remove(r)
'''

# ---------------------------------------------------------------- hunk 6
# region_ast_generator.py：链首块 import 前缀去重（镜像 cond_block 守卫）
H6_OLD = '''                if _last_store_idx >= 0:
                    _pred_instrs = instrs[:_last_store_idx + 1]
                    _cond_instrs = instrs[_last_store_idx + 1:]
                    _pred_stmts = self._build_statements_from_instructions(_pred_instrs)
                    if _pred_stmts:
                        pre_stmts.extend(_pred_stmts)
                        instrs = _cond_instrs
'''

H6_NEW = '''                if _last_store_idx >= 0:
                    _pred_instrs = instrs[:_last_store_idx + 1]
                    _cond_instrs = instrs[_last_store_idx + 1:]
                    _pred_stmts = self._build_statements_from_instructions(_pred_instrs)
                    # [r186-OROFANDS-cpl] 与 _generate_ternary 的 cond_block import
                    # 前导守卫同判据（镜像）：条件链首块若就是 TernaryRegion 的
                    # entry 且其 import 前缀已由 generate() 预扫描提取
                    # （_entry_import_extracted_blocks），此处不再重复抽取
                    # Import/ImportFrom——否则同一条 `import sys` 出现两次
                    # （违反每块唯一归属）。判据只读「该块已登记」这一发射状态
                    # + 语句类型，未命中时逐字节不变（C3）。
                    if cb in self._entry_import_extracted_blocks:
                        _pred_stmts = [s for s in _pred_stmts
                                       if s.get('type') not in ('Import', 'ImportFrom')]
                    if _pred_stmts:
                        pre_stmts.extend(_pred_stmts)
                        instrs = _cond_instrs
                    elif _last_store_idx >= 0:
                        instrs = _cond_instrs
'''

PATCHES = [
    (RAG, H1_OLD, H1_NEW, 'hunk1 _ternary_chain_completion',
     'def _ternary_chain_completion(block):'),
    (RAG, H2_OLD, H2_NEW, 'hunk2 _can_be_ternary_header',
     'and _ternary_chain_completion(block) is not None'),
    (RAG, H3_OLD, H3_NEW, 'hunk3 chain completion channel',
     '_ofc_result = _ternary_chain_completion(block)'),
    (RAG, H4_OLD, H4_NEW, 'hunk4 op_chain replacement gate',
     'and not _ofc_completed:'),
    (RAG, H5_OLD, H5_NEW, 'hunk5 dissolve subsumed BoolOpRegion',
     'for _bl in (boolop_regions, conditional_regions):'),
    (RAG2, H6_OLD, H6_NEW, 'hunk6 import prefix dedupe',
     'if cb in self._entry_import_extracted_blocks:'),
]


def sha256(path):
    with open(path, 'rb') as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def read_text(path):
    raw = open(path, 'rb').read()
    has_bom = raw.startswith(b'\xef\xbb\xbf')
    text = raw.decode('utf-8-sig')
    return text, has_bom


def write_text(path, text, has_bom):
    data = text.encode('utf-8')
    if has_bom:
        data = b'\xef\xbb\xbf' + data
    with open(path, 'wb') as fh:
        fh.write(data)


def apply(direction):
    """direction='apply' 用 old→new；'revert' 用 new→old。

    状态判据用各 hunk 的 marker（新文本独有片段），保证幂等与可逆：
      apply  : marker 已在 ⇒ 跳过；否则 old 必须恰好出现 1 次（count==1）；
      revert : marker 不在 ⇒ 跳过；否则 new 必须恰好出现 1 次。
    （插入式 hunk 的 new 文本包含 old 文本，故不能用 count(old) 判状态。）
    """
    grouped = []          # [(path, [(src, dst, tag), ...], has_bom, text)]
    index = {}
    for path, old, new, tag, marker in PATCHES:
        src, dst = (old, new) if direction == 'apply' else (new, old)
        if path not in index:
            text, has_bom = read_text(path)
            index[path] = len(grouped)
            grouped.append((path, [], has_bom, text))
        entry = grouped[index[path]]
        applied = marker in entry[3]
        if (direction == 'apply' and applied) or (direction == 'revert' and not applied):
            print('[skip] %-44s already %sd'
                  % (tag, 'applied' if direction == 'apply' else 'reverted'))
            continue
        n = entry[3].count(src)
        if n != 1:
            raise SystemExit('[fatal] %s: anchor count=%d for %s (%s)'
                             % (path, n, tag, direction))
        entry[1].append((src, dst, tag))
    pending = [g for g in grouped if g[1]]
    if not pending:
        print('[noop] nothing to change')
        return 0
    before = {g[0]: sha256(g[0]) for g in pending}
    for path, repls, has_bom, text in pending:
        for src, dst, tag in repls:
            text = text.replace(src, dst, 1)
            print('[%-6s] %-40s %s' % (direction, tag, os.path.basename(path)))
        write_text(path, text, has_bom)
    import tempfile
    tmpdir = tempfile.mkdtemp(prefix='fix186_')
    for path in before:
        try:
            py_compile.compile(path, cfile=os.path.join(tmpdir, 'x.pyc'), doraise=True)
        except py_compile.PyCompileError as exc:
            print('[fatal] py_compile failed: %s' % exc)
            return 1
    for path in before:
        print('  %-46s sha256 %s -> %s'
              % (os.path.relpath(path, REPO), before[path][:16], sha256(path)[:16]))
        head = open(path, 'rb').read(3)
        assert head == b'\xef\xbb\xbf', 'BOM lost in %s' % path
    print('[ok] %s done' % direction)
    return 0


def main(argv):
    if '--revert' in argv:
        return apply('revert')
    return apply('apply')


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
