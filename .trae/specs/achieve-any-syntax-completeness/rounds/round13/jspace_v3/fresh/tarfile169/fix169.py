#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r169 修 tarfile「族 D：循环区归属」（`TarFile.__init__` + `TarFile._load`）。

两处根因都与 RECON167 的假定不同（实证见 r169/work/*.txt 的 dis/探针记录）
------------------------------------------------------------------------
D1（`TarFile._load`，16 vs 11 指令）：真因不在 `_loop_handle_header:12903`
  （该函数正常返回），而在 `_loop_handle_header` 的 if-break **指令级回退段**
  （"header 尾 = 条件跳转 + 一个后继是 break/return 出口 + 另一个后继是回边"
  → `_loop_process_header_instructions` 之外的 13357–13475 手写路径）。
  该段的后向扫描只认 `POP_TOP/RETURN_VALUE/RETURN_CONST`（表达式语句收尾）
  与 `COMPARE_OP/IS_OP/...`（条件起点）为语句边界；`TarFile._load` 的 header
  块是 `while True:` 的「体首语句 + 条件求值」合块
  （`self.next()`→STORE_FAST tarinfo→LOAD_FAST tarinfo→POP_JUMP_FORWARD_IF_NOT_NONE），
  赋值收尾的 `STORE_FAST` 不被认作边界 ⇒ `_stmt_end` 停在 len，整段前缀被当
  条件表达式重建 ⇒ 头语句整条蒸发、条件退化成裸名字 `tarinfo`（-8/+3 = -5）。
  修复 [v169-WHILEHEAD]：把 `STORE_*` 也当语句边界（排除 walrus 的 `COPY 1`
  前置），切出的前导语句走既有 `_acc → _build_statement` 分支正常发射。
  修复 [v169-NONECHK]：条件跳转为 `POP_JUMP_*_IF_NONE/IF_NOT_NONE`（3.11 把
  `x is None` 融合进跳转、没有 COMPARE_OP）时，按「臂块 == 跳转目标 ⟹ 臂在条件
  成立侧执行」重建 `Compare(ops=[Is/IsNot], comparators=[Constant(None)])`；
  取反只能用既有 `_flip_is_none_compare`（用 not() 会多出 UNARY_NOT，重编译退化
  为 `UNARY_NOT + POP_JUMP_IF_FALSE`）。

D2（`TarFile.__init__`，323 vs 329 指令 + EXTENDED_ARG + 异常表 DIFF）：
  分析层是对的（`IfRegion@972 merge=1346`），坏在发射端归属：
  `_r58_collect_break_target_stmts(@9206)` 把循环 break 目标块（正是外层
  `IfRegion@972` 的 merge_block 1346）的语句收进「循环后顺序语句」，
  `_loop_generate_while` 把它并入自己的返回列表，父 `If` 的 then 体随即把整块
  吞进 `if self.mode == 'a':` 体内（`if self.mode in ('a','w','x')` 错位嵌套）。
  只跳过收集不够：`_generate_loop` 的成员块收尾扫（只登记不发射）会把 1346 标记
  generated，外层序列随后跳过它 ⇒ 语句蒸发。
  修复：新增判据 `_v169_post_loop_parent_if(region, block)` —— 纯结构事实
  （`region.parent` 是 IfRegion 且 `block is parent.merge_block`）；merge 是两臂
  汇合点，then 臂内循环的 break 目标 == merge ⟹ 臂内循环之后没有别的语句，
  break 直接跳出整个 if ⟹ 该块语句属**外层序列**（If 之后）。同判据在收集侧
  （`_r58_collect_break_target_stmts`）与登记侧（`_generate_loop` 收尾扫）同时
  生效：既不收进循环返回值，也不被「只登记不发射」吞掉，交外层序列在 If 之后
  按正常顺序发射。

读数（本轮实测）
----------------
  tarfile 152/160 → **154/160**；`TarFile._load` EQUAL、`TarFile.__init__` EQUAL。
  四语料 request 194/194、difflib 62/62、cookiejar 91/105、subprocess 69/78，
  产物与改前逐字节 SAME。458 电池无新增回归。

用法
----
  python -I -X utf8 fix169.py          # 打补丁（幂等）
  python -I -X utf8 fix169.py --check  # 只检查当前状态
"""
import os
import py_compile
import sys
import tempfile

REPO = r'F:\Downloads\pythoncdc-main'
TARGET = os.path.join(REPO, 'core', 'cfg', 'region_ast_generator.py')

MARKER = '_v169_post_loop_parent_if'

# ---- 1) pristine line 7831 : +9 lines ----
A1 = """            for block in region.blocks:
                if block not in region.else_blocks:
                    if exclude_blocks is None or block not in exclude_blocks:
                        block_region = self.region_analyzer.get_region_for_block(block)
                        if (block_region and 
                            block_region != region and 
                            not isinstance(block_region, LoopRegion) and
                            (block_region.parent == region or 
                             (block_region.parent is not None and isinstance(block_region, (WithRegion, TryExceptRegion))))):
                            continue
                        self.generated_blocks.add(block)

            return result
        finally:
            self._generating_regions.discard(region_id)
            self._generated_regions.add(region_id)
            self._loop_depth -= 1
            self._current_loop = saved_loop

"""

R1 = """            for block in region.blocks:
                if block not in region.else_blocks:
                    if exclude_blocks is None or block not in exclude_blocks:
                        block_region = self.region_analyzer.get_region_for_block(block)
                        if (block_region and 
                            block_region != region and 
                            not isinstance(block_region, LoopRegion) and
                            (block_region.parent == region or 
                             (block_region.parent is not None and isinstance(block_region, (WithRegion, TryExceptRegion))))):
                            continue
                        # [v169-POSTLOOP] 与 _r58_collect_break_target_stmts
                        # 同一判据（_v169_post_loop_parent_if）：break 目标 ==
                        # 外层 IfRegion.merge 的块属外层序列，本扫尾只登记不
                        # 发射的语义在此块上会把它整体吞掉（父 If 已收尾、
                        # 外层序列随后走查到该块时被 generated 守卫跳过 ⇒
                        # 语句蒸发）。跳过登记，交外层序列在 If 之后按正常
                        # 顺序发射；未命中判据时行为逐位不变（C3）。
                        if self._v169_post_loop_parent_if(region, block) is not None:
                            continue
                        self.generated_blocks.add(block)

            return result
        finally:
            self._generating_regions.discard(region_id)
            self._generated_regions.add(region_id)
            self._loop_depth -= 1
            self._current_loop = saved_loop

"""

# ---- 2) pristine line 9198 : +30 lines ----
A2 = '''            if _r9_for_shell is not None:
                return _r9_for_shell

        if pre_stmts or _sequential_after_loop:
            output = list(pre_stmts)
            output.append(result)
            output.extend(_sequential_after_loop)
            return output
        return result

    def _r58_collect_break_target_stmts(self, region: LoopRegion, body_set: set) -> List[Dict[str, Any]]:
        """[R58-B] 收集 while/for 非平凡 break 目标块的顺序语句。

        识别条件——region.has_break=True 且 break 目标块含非平凡代码
        （非 PURE_JUMP/条件跳转/POP_TOP/EXTENDED_ARG 清理），该块是
        循环后顺序代码入口（如 default_event_source while@2476 的
        break 目标 3214 = `dt = date.replace; yield AFTER_TRADING_END`）。
        归约方式——查找以其为 entry 的 If/Loop/Try 区域则递归生成，
        否则直接生成块语句及其非 RETURN 后继；标记 generated 防重复。
        AST 映射——返回语句列表，调用方追加到循环节点之后。'''

R2 = '''            if _r9_for_shell is not None:
                return _r9_for_shell

        if pre_stmts or _sequential_after_loop:
            output = list(pre_stmts)
            output.append(result)
            output.extend(_sequential_after_loop)
            return output
        return result

    def _v169_post_loop_parent_if(self, region: LoopRegion, block: BasicBlock):
        """[v169-POSTLOOP] 循环后顺序语句归属外层 If 的判据：返回外层 IfRegion 或 None。

        ①算法依据：No More Gotos 区域归约四原则——原则 2（每块唯一归属）、
        原则 4（父引用子入口）。IfRegion 的 merge_block 是两臂汇合点：then 臂
        内循环的 break 目标 == merge ⟹ 臂内循环之后没有别的语句，break 直接
        跳出整个 if；该块的语句因此属于**外层序列**（If 之后），不属 if 的
        then 臂，也不属循环区域的「循环后顺序语句」返回值。
        ②归约顺序：本判据只做归属裁决（不发射、不登记），由调用方决定
        （收集侧跳过收集 / 收尾扫跳过登记），块的发射交外层序列按正常顺序
        在 If 之后进行。
        ③唯一归属判定：纯结构事实——region.parent 的类型 + break 目标块
        与 parent.merge_block 的同一性（I.4 白名单），无偏移阈值、无名字白名单。
        ④嵌套处理：仅直接父区域为 IfRegion 时成立；更远祖先、循环/with/try
        父级一律返回 None（旧行为）。
        ⑤入口引用语义：返回的是父 IfRegion 本身（父引用子入口的反向引用），
        调用方只用它做块同一性比较。
        ⑥反编译流程：区域生成层——供 _r58_collect_break_target_stmts（收集
        侧）与 _generate_loop 的成员块收尾扫（登记侧）共用的同一事实源。
        C 条款：[C1] 只读 parent/merge_block/块同一性；[C2] 判据命中才改变
        归属，未命中返回 None、旧路径逐位不变（C3 封闭）。
        """
        _par = getattr(region, 'parent', None)
        if not isinstance(_par, IfRegion):
            return None
        _mg = getattr(_par, 'merge_block', None)
        if _mg is None or block is not _mg:
            return None
        return _par

    def _r58_collect_break_target_stmts(self, region: LoopRegion, body_set: set) -> List[Dict[str, Any]]:
        """[R58-B] 收集 while/for 非平凡 break 目标块的顺序语句。

        识别条件——region.has_break=True 且 break 目标块含非平凡代码
        （非 PURE_JUMP/条件跳转/POP_TOP/EXTENDED_ARG 清理），该块是
        循环后顺序代码入口（如 default_event_source while@2476 的
        break 目标 3214 = `dt = date.replace; yield AFTER_TRADING_END`）。
        归约方式——查找以其为 entry 的 If/Loop/Try 区域则递归生成，
        否则直接生成块语句及其非 RETURN 后继；标记 generated 防重复。
        AST 映射——返回语句列表，调用方追加到循环节点之后。'''

# ---- 3) pristine line 9215 : +15 lines ----
A3 = '''        归约方式——查找以其为 entry 的 If/Loop/Try 区域则递归生成，
        否则直接生成块语句及其非 RETURN 后继；标记 generated 防重复。
        AST 映射——返回语句列表，调用方追加到循环节点之后。
        """
        sequential: List[Dict[str, Any]] = []
        if not getattr(region, 'has_break', False):
            return sequential
        processed = set()
        for bb in region.break_blocks:
            if bb in body_set or bb.start_offset in processed:
                continue
            meaningful = [i for i in bb.instructions
                          if i.opname not in NOISE_OPS
                          and i.opname not in PURE_JUMP_OPS
                          and i.opname not in CONDITIONAL_JUMP_OPS
                          and i.opname not in ('POP_TOP', 'EXTENDED_ARG')]
            if not meaningful:
                continue
            bb_region = (self.region_analyzer.get_entry_region_for_block(bb)
                         or self.region_analyzer.get_region_for_block(bb))'''

R3 = '''        归约方式——查找以其为 entry 的 If/Loop/Try 区域则递归生成，
        否则直接生成块语句及其非 RETURN 后继；标记 generated 防重复。
        AST 映射——返回语句列表，调用方追加到循环节点之后。
        """
        sequential: List[Dict[str, Any]] = []
        if not getattr(region, 'has_break', False):
            return sequential
        processed = set()
        for bb in region.break_blocks:
            if bb in body_set or bb.start_offset in processed:
                continue
            # [v169-POSTLOOP] 区域归约算法原则 2（每块唯一归属）/ 原则 4
            # （父引用子入口）：break 目标块恰是**外层 IfRegion 的 merge_block**
            # 时，循环之后的顺序代码位于该 if 之外，不属于 if 的 then 臂。
            # 判据见 _v169_post_loop_parent_if（纯结构事实：IfRegion 的 merge
            # 是两臂汇合点——then 臂内循环的 break 目标 == merge ⟹ 臂内循环
            # 之后没有别的语句，break 直接跳出整个 if）。此时若仍把该块语句
            # 收进本循环的"循环后顺序语句"并随 _generate_loop 返回值交给父 If，
            # 父 If 的 then 体把它 extend 进体内（TarFile.__init__ 实测：
            # `if self.mode in ('a','w','x')` 整块被搬进 `if self.mode == 'a':`
            # 体内、EXTENDED_ARG 错位 +6 指令）。归约方式——不入本循环的
            # sequential（也不登记 generated_blocks），交外层序列按正常顺序
            # 在 If 之后发射；同判据也用于 _generate_loop 的成员块收尾扫，
            # 防止该块被「只登记不发射」的扫尾吞掉。未命中时行为逐位不变（C3）。
            if self._v169_post_loop_parent_if(region, bb) is not None:
                continue
            meaningful = [i for i in bb.instructions
                          if i.opname not in NOISE_OPS
                          and i.opname not in PURE_JUMP_OPS
                          and i.opname not in CONDITIONAL_JUMP_OPS
                          and i.opname not in ('POP_TOP', 'EXTENDED_ARG')]
            if not meaningful:
                continue
            bb_region = (self.region_analyzer.get_entry_region_for_block(bb)
                         or self.region_analyzer.get_region_for_block(bb))'''

# ---- 4) pristine line 13367 : +21 lines ----
A4 = """                        pre_cond_instrs = [i for i in instrs if i != jump_instr]
                        if pre_cond_instrs:
                            _stmt_end = len(pre_cond_instrs)
                            for _si in range(len(pre_cond_instrs) - 1, -1, -1):
                                if pre_cond_instrs[_si].opname in ('POP_TOP', 'RETURN_VALUE', 'RETURN_CONST'):
                                    _stmt_end = _si + 1
                                    break
                                if pre_cond_instrs[_si].opname in ('COMPARE_OP', 'IS_OP', 'IS_NOT', 'CONTAINS_OP', 'NOT_OP', 'UNARY_NOT'):
                                    _stmt_end = _si
                                    break
                            if _stmt_end > 0 and _stmt_end < len(pre_cond_instrs):
                                _leading = pre_cond_instrs[:_stmt_end]
                                _cond_instrs = pre_cond_instrs[_stmt_end:]
                                _acc = []
                                for _li in _leading:
                                    _acc.append(_li)
                                    if _li.opname in ('POP_TOP', 'STORE_NAME', 'STORE_FAST', 'STORE_GLOBAL', 'STORE_DEREF', 'STORE_DEREF', 'RETURN_VALUE', 'RETURN_CONST'):
                                        # [r20-r51] 前导窗口含 IMPORT_NAME 时必须走公共 import 状态机；
                                        # _build_statement 会把 LOAD_CONST(fromlist)+STORE_FAST 读成 NAME = (fromlist,) 赋值、
                                        if any(_ai.opname == 'IMPORT_NAME' for _ai in _acc):"""

R4 = """                        pre_cond_instrs = [i for i in instrs if i != jump_instr]
                        if pre_cond_instrs:
                            _stmt_end = len(pre_cond_instrs)
                            for _si in range(len(pre_cond_instrs) - 1, -1, -1):
                                if pre_cond_instrs[_si].opname in ('POP_TOP', 'RETURN_VALUE', 'RETURN_CONST'):
                                    _stmt_end = _si + 1
                                    break
                                if pre_cond_instrs[_si].opname in ('COMPARE_OP', 'IS_OP', 'IS_NOT', 'CONTAINS_OP', 'NOT_OP', 'UNARY_NOT'):
                                    _stmt_end = _si
                                    break
                                # [v169-WHILEHEAD] 区域归约算法原则 2（每块唯一归属）：
                                # `while True:` 的 header 块把循环体首语句与循环条件求值
                                # 放在同一块（3.11 不为无条件循环另设条件块），故前导赋值
                                # 语句以 STORE_* 收尾时该 STORE 即「语句边界」。旧判据只认
                                # POP_TOP/RETURN（表达式语句）与 COMPARE_OP/IS_OP（条件起
                                # 点），赋值形态下 _stmt_end 停在 len(pre_cond_instrs)，整段
                                # 前缀被当成条件表达式重建 ⇒ 前导语句静默蒸发、条件退化为
                                # 裸名字（TarFile._load 实测：`tarinfo = self.next()` 整条
                                # 消失且 `is None` 极性丢失）。判据只读本块指令序（I.4）：
                                # 相邻 STORE_* 且其前不是 walrus 的 COPY 1（`if (n := f()):`
                                # 的赋值属条件本身，不得切出）。未命中边界时 _stmt_end 维持
                                # len，旧路径逐位不变（C3）。
                                if (pre_cond_instrs[_si].opname
                                        in ('STORE_FAST', 'STORE_NAME',
                                            'STORE_GLOBAL', 'STORE_DEREF')):
                                    if (_si > 0
                                            and pre_cond_instrs[_si - 1].opname == 'COPY'
                                            and pre_cond_instrs[_si - 1].arg == 1):
                                        continue
                                    _stmt_end = _si + 1
                                    break
                            if _stmt_end > 0 and _stmt_end < len(pre_cond_instrs):
                                _leading = pre_cond_instrs[:_stmt_end]
                                _cond_instrs = pre_cond_instrs[_stmt_end:]
                                _acc = []
                                for _li in _leading:
                                    _acc.append(_li)
                                    if _li.opname in ('POP_TOP', 'STORE_NAME', 'STORE_FAST', 'STORE_GLOBAL', 'STORE_DEREF', 'STORE_DEREF', 'RETURN_VALUE', 'RETURN_CONST'):
                                        # [r20-r51] 前导窗口含 IMPORT_NAME 时必须走公共 import 状态机；
                                        # _build_statement 会把 LOAD_CONST(fromlist)+STORE_FAST 读成 NAME = (fromlist,) 赋值、
                                        if any(_ai.opname == 'IMPORT_NAME' for _ai in _acc):"""

# ---- 5) pristine line 13454 : +30 lines ----
A5 = """                                # 其余跳转形态维持旧行为（C3）。
                                _er_jump_op = jump_instr.opname if jump_instr is not None else ''
                                if (_er_jump_op in ('POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
                                                    'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE')
                                        and _break_or_return_block is not None
                                        and getattr(jump_instr, 'argval', None) is not None):
                                    _er_ret_on_true = ((_er_jump_op.endswith('IF_TRUE')) ==
                                                       (jump_instr.argval == _break_or_return_block.start_offset))
                                    if not _er_ret_on_true:
                                        test_expr = {'type': 'UnaryOp', 'op': 'not', 'operand': test_expr}
                                if _return_val is not None:
                                    body_stmts.append({
                                        'type': 'If',
                                        'test': test_expr,
                                        'body': [{'type': 'Return', 'value': _return_val}],
                                        'orelse': []
                                    })
                                else:
                                    body_stmts.append({
                                        'type': 'If',"""

R5 = """                                # 其余跳转形态维持旧行为（C3）。
                                _er_jump_op = jump_instr.opname if jump_instr is not None else ''
                                if (_er_jump_op in ('POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
                                                    'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE')
                                        and _break_or_return_block is not None
                                        and getattr(jump_instr, 'argval', None) is not None):
                                    _er_ret_on_true = ((_er_jump_op.endswith('IF_TRUE')) ==
                                                       (jump_instr.argval == _break_or_return_block.start_offset))
                                    if not _er_ret_on_true:
                                        test_expr = {'type': 'UnaryOp', 'op': 'not', 'operand': test_expr}
                                # [v169-NONECHK] 区域归约算法原则 2（每块唯一归属）+
                                # AST 映射保真：CPython 3.11 的 `x is None` 检测被融合进
                                # POP_JUMP_*_IF_NONE / IF_NOT_NONE（无 COMPARE_OP），故
                                # 条件表达式重建后只剩裸名字。本手写路径若照搬真值取反，
                                # `while True: tarinfo = self.next(); if tarinfo is None:
                                # break` 会被发射成 `if tarinfo: break`——`is None` 的
                                # 身份语义丢失且极性反转（TarFile._load 实测）。判据只读
                                # 跳转指令 opname + 臂块偏移（结构事实，无名字/偏移特例）：
                                #   跳转条件 = `expr is not None`(IF_NOT_NONE) / `is None`
                                #   (IF_NONE)；臂块 == 跳转目标 ⟶ 臂在条件成立时执行，
                                #   否则臂在落空侧执行 ⟹ 取反。None 类比较的取反只能翻转
                                #   运算符（_flip_is_none_compare），用 not() 会多出
                                #   UNARY_NOT 使重编译退化为 `UNARY_NOT +
                                #   POP_JUMP_IF_FALSE`；未命中 None 类跳转时行为逐位不变（C3）。
                                if (_er_jump_op in ('POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_BACKWARD_IF_NONE',
                                                    'POP_JUMP_FORWARD_IF_NOT_NONE', 'POP_JUMP_BACKWARD_IF_NOT_NONE',
                                                    'POP_JUMP_IF_NONE', 'POP_JUMP_IF_NOT_NONE')
                                        and _break_or_return_block is not None
                                        and getattr(jump_instr, 'argval', None) is not None):
                                    _er_none_cond = {
                                        'type': 'Compare',
                                        'left': test_expr,
                                        'ops': [{'type': ('IsNot' if 'IF_NOT_NONE' in _er_jump_op
                                                          else 'Is')}],
                                        'comparators': [{'type': 'Constant', 'value': None}],
                                    }
                                    if jump_instr.argval == _break_or_return_block.start_offset:
                                        test_expr = _er_none_cond
                                    else:
                                        test_expr = _flip_is_none_compare(_er_none_cond)
                                if _return_val is not None:
                                    body_stmts.append({
                                        'type': 'If',
                                        'test': test_expr,
                                        'body': [{'type': 'Return', 'value': _return_val}],
                                        'orelse': []
                                    })
                                else:
                                    body_stmts.append({
                                        'type': 'If',"""

ANCHORS = ((A1, R1), (A2, R2), (A3, R3), (A4, R4), (A5, R5))


def main():
    only_check = '--check' in sys.argv
    raw = open(TARGET, 'rb').read()
    has_bom = raw.startswith(b'\xef\xbb\xbf')
    text = raw.decode('utf-8-sig' if has_bom else 'utf-8')
    nl = '\r\n' if '\r\n' in text else '\n'
    norm = text.replace('\r\n', '\n')

    if MARKER in norm:
        print('[fix169] already applied (marker present) — no change')
        return 0

    for a, _r in ANCHORS:
        n = norm.count(a)
        if n != 1:
            print('[fix169] FAILED: anchor count=%d (expected 1): %r' % (n, a.strip()[:60]))
            return 2

    new_norm = norm
    for a, r in ANCHORS:
        new_norm = new_norm.replace(a, r)
    if only_check:
        print('[fix169] check: patchable (all %d anchors count=1), not applied' % len(ANCHORS))
        return 0

    out = new_norm.replace('\n', nl).encode('utf-8')
    expect = raw
    for a, r in ANCHORS:
        expect = expect.replace(a.replace('\n', nl).encode('utf-8'),
                                r.replace('\n', nl).encode('utf-8'))
    if out != expect:
        print('[fix169] FAILED: byte-level round-trip mismatch')
        return 3
    inserted = sum(r.count('\n') - a.count('\n') for a, r in ANCHORS)
    if out.count(nl.encode()) != raw.count(nl.encode()) + inserted:
        print('[fix169] FAILED: line-count accounting mismatch')
        return 4

    tmpdir = tempfile.mkdtemp(prefix='fix169_')
    tmp_py = os.path.join(tmpdir, 'patched.py')
    with open(tmp_py, 'wb') as f:
        f.write(out)
    try:
        py_compile.compile(tmp_py, cfile=tmp_py + 'c', doraise=True, optimize=0)
    except py_compile.PyCompileError as exc:
        print('[fix169] FAILED: patched source does not compile: %s' % exc)
        return 5

    with open(TARGET, 'wb') as f:
        f.write(out)
    try:
        py_compile.compile(TARGET, cfile=tmp_py + 'c2', doraise=True, optimize=0)
    except py_compile.PyCompileError as exc:
        with open(TARGET, 'wb') as f:
            f.write(raw)
        print('[fix169] ROLLED BACK: target does not compile: %s' % exc)
        return 6

    print('[fix169] applied: +%d lines, py_compile OK (%s%s)' % (
        inserted, TARGET, ', BOM preserved' if has_bom else ''))
    return 0


if __name__ == '__main__':
    sys.exit(main())
