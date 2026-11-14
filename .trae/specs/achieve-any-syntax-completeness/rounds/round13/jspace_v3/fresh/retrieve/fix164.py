# -*- coding: utf-8 -*-
"""rr-v5r164 fix: (1) 链内「极性融合 not 头」的 or 子组截断（NOTMIX 非链首残形）；
(2) 值上下文 BoolOp 汇合块的元组解包目标（UNPACK_SEQUENCE）。

== 目标单元 ==
urllib.request.URLopener.retrieve 的守卫
    if filename is None and (not type or type == 'file'):
当前被压平成 `A and type and type == 'file'`，并叠加重复 open。

== 修复 1（region_analyzer.py，方案 A：截断外层链）==
r163 RECON 已实证：`_detect_boolop_conditional_chain` 按末指令 opcode 把
`not type` 的测试块标成 'and' 并压平整条链；v161-NOTMIX 探测只管链首，其
等价出口判据也会把「空体」形（`pass` 体）排除。

在成员追加点（`chain.append((current, op_type))` 之前）识别「not X or Y」
内层 or 组的块级签名并在此截断：
  当前成员 M 以 FALSE 极性条件跳转收尾，短路目标 T；
  M 的落空后继 F 同样以 FALSE 极性收尾，短路目标 E；
  F 的落空后继 == T（同一真出口），且 T、E 是不同块；
  T 与 E 不等价，或 T 是「空体跳板」（仅噪声指令、唯一后继恰为 E，即
  `pass` 体 / 空 then 臂）；
  T 不是链内既有成员的跳转目标（排除 `A or not B or C` 这类合法 or 链）。
命中且链已非空 ⇒ `break`（前缀仍按既有流程归约，长度 <2 时返回 None）；
命中且 M 是链首（整组即 `not X or Y` 且体为空体跳板）⇒ 返回 None。
不命中逐字节回退现状（C3）。判据只读块末 opcode / 跳转目标 / 后继身份 /
块内噪声指令集 / 链内既有目标（I.4 白名单）。

== 修复 2（region_ast_generator.py，元组解包目标）==
retrieve 的 `garbage, path = _splithost(path or "")` 等三条语句里带 `or`
短路（值上下文 BoolOpRegion），其 merge 块为
`[PRECALL, CALL, UNPACK_SEQUENCE 2, STORE garbage, STORE path, ...]`。
`_generate_boolop_impl` 的 value_target 分支把 merge 块首个 STORE 当作唯一
目标发射 `garbage = _splithost(path or '')`，UNPACK_SEQUENCE 与第二个
STORE 丢失（判官 Different bytecode，剩余唯一失败单元）。判据只读 merge 块
指令序列结构（UNPACK_SEQUENCE/UNPACK_EX + 紧随的 N 个 STORE_*），命中即发射
`Assign(targets=[Tuple(...)], value=<合并 Call 表达式>)`；收集不全逐位回退
既有单目标发射（C3）。

用法: D:/Python/python.exe -I -X utf8 D:\temp\opencode\cl_layout\r164\fix164.py
"""

import os
import py_compile
import sys

ANALYZER = r'F:\Downloads\pythoncdc-main\core\cfg\region_analyzer.py'
GENERATOR = r'F:\Downloads\pythoncdc-main\core\cfg\region_ast_generator.py'

ANCHOR_CHAIN = (
    "                if not _b115_reeval:\n"
    "                    break\n"
    "            chain.append((current, op_type))\n"
)

PATCH_CHAIN = '''                if not _b115_reeval:
                    break
            # [v164-NOTMIXTAIL] 「极性融合 not 头」的 or 子组截断（NOTMIX 非链首
            # 残形）。①算法依据：CPython 对 `A and (not X or Y)` 的降级把
            #   `not X` 的假边（X 为假 ⇒ 内层 or 组为真 ⇒ 整链为真）直达 then 体
            #   T，而不是外层 and 链的共享假出口 E；`Y` 的假边才落到 E，其落空
            #   后继同为 T。按末指令 opcode 只能得到 'and'（POP_JUMP_IF_FALSE），
            #   整条链被压平成 `A and X and Y`——X 为假时源码进体、渲染跳过，
            #   语义反转（实模块叠加重复 open）。链首形由 v161-NOTMIX 的
            #   _detect_fused_not_head_chain 承担，本处只补**非链首**成员与
            #   「空体」整组这两个缺口。
            # ②归约顺序：成员准入点（chain.append 之前）判定，命中即在本成员处
            #   截断外层链；BoolOp 先于 Conditional 归约的既有顺序不变。
            # ③唯一归属判定：被截断的本成员及其后续块不并入本链，回到 IfRegion
            #   层级按 then/else 整块归约（原则 2 每块唯一归属、原则 3 嵌套即
            #   抽象节点）；前缀成员仍归本 BoolOpRegion，长度不足 2 时整链不产
            #   区域（交还 IfRegion）。
            # ④嵌套处理：内层 `not X or Y` 由嵌套 BoolOp/IfRegion 经其 entry
            #   独立重建，外层条件只引用前缀的 entry。
            # ⑤入口引用语义：前缀链 entry 不变；被截断块不作为外层操作数。
            # ⑥反编译流程：region_analyzer 归约 → AST（If.test 为
            #   `A and (not X or Y)` 或其等价嵌套形）。
            # 判据（[C1] 只读块末 opcode 族/跳转目标/后继身份/块内噪声 opcode
            #   集/链内既有目标）：当前成员 FALSE 极性、目标 T；落空后继 F 亦
            #   FALSE 极性、目标 E；F 的落空后继恰为 T（同一真出口）；T、E 为
            #   不同块；(T、E 非等价出口 或 T 是唯一的「空体跳板」——仅噪声
            #   指令且唯一后继恰为 E)；T 不是链内既有成员的跳转目标（排除合法
            #   `A or not B or C`——首成员与 `not B` 共享真出口 T）。非链首成员
            #   命中即截断；链首命中（整组即 `not X or Y` 且体为空体跳板）即整
            #   链交还 IfRegion。任一校验不命中逐字节回退现状（[C3]）。
            if last.opname in ('POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_IF_FALSE'):
                _v164_trunc = False
                _v164_pair = False
                if getattr(last, 'argval', None) is not None:
                    _v164_t = self.cfg.get_block_by_offset(last.argval)
                    _v164_f = None
                    for _v164_s in current.conditional_successors:
                        if _v164_s.start_offset != last.argval:
                            _v164_f = _v164_s
                            break
                    if (_v164_t is not None and _v164_f is not None
                            and _v164_f is not current):
                        _v164_fli = _v164_f.get_last_instruction()
                        if (_v164_fli is not None
                                and _v164_fli.opname in ('POP_JUMP_FORWARD_IF_FALSE',
                                                         'POP_JUMP_IF_FALSE')
                                and getattr(_v164_fli, 'argval', None) is not None):
                            _v164_e = self.cfg.get_block_by_offset(_v164_fli.argval)
                            _v164_fft = None
                            for _v164_s in _v164_f.conditional_successors:
                                if _v164_s.start_offset != _v164_fli.argval:
                                    _v164_fft = _v164_s
                                    break
                            _v164_tramp = False
                            if _v164_e is not None and _v164_e is not _v164_t:
                                _v164_exc = set(getattr(_v164_t,
                                                        'exception_successors', None) or ())
                                _v164_tsucc = [s for s in _v164_t.successors
                                               if s not in _v164_exc]
                                _v164_tramp = bool(
                                    all(i.opname in ('NOP', 'CACHE', 'EXTENDED_ARG', 'RESUME')
                                        for i in _v164_t.instructions)
                                    and len(_v164_tsucc) == 1
                                    and _v164_tsucc[0] is _v164_e)
                            _v164_prev_tgts = set()
                            for _v164_pb, _ in chain:
                                _v164_pl = _v164_pb.get_last_instruction()
                                if (_v164_pl is not None
                                        and getattr(_v164_pl, 'argval', None) is not None):
                                    _v164_prev_tgts.add(_v164_pl.argval)
                            _v164_sig = bool(
                                _v164_e is not None
                                and _v164_fft is _v164_t
                                and _v164_e is not _v164_t
                                and (not self._is_equivalent_exit_block(_v164_e, _v164_t)
                                     or _v164_tramp))
                            if _v164_sig:
                                if chain:
                                    _v164_trunc = _v164_t.start_offset not in _v164_prev_tgts
                                else:
                                    _v164_pair = _v164_tramp
                if _v164_pair:
                    return None
                if _v164_trunc:
                    if len(chain) < 2:
                        return None
                    break
            chain.append((current, op_type))
'''

HELPER_ANCHOR = (
    "    def _generate_boolop(self, region: BoolOpRegion, skip_store_targets: Set[str] = None)"
    " -> Optional[List[Dict[str, Any]]]:\n"
)

HELPER = '''    def _boolop_unpack_targets_at_join(self, region: 'BoolOpRegion') -> Optional[Dict[str, Any]]:
        """[v164-UNPACKTGT] 值上下文 BoolOp 汇合块的元组解包赋值目标（Tuple）。

        ①算法依据：CPython 对 `x, y = f(a or b)` 生成
          `[.. f/CALL ..] UNPACK_SEQUENCE 2; STORE x; STORE y`——UNPACK 与
          其后 N 个 STORE 共同构成**一个**赋值目标（元组解包），不是 N 条独立
          赋值。值上下文 BoolOpRegion 的汇合块正是 `UNPACK + STORE 段`
          所在块，而 `_generate_boolop_impl` 的 value_target 分支只取汇合块
          首个 STORE 作单目标，UNPACK 与其余 STORE 一并丢失（实测
          urllib.request.URLopener.retrieve 的三条
          `garbage, path = _splithost(path or "")` 退化为
          `garbage = _splithost(path or '')`，判官 Different bytecode）。
        ②归约顺序：由 value_target 分支在拼接 rhs 前调用，只产出一个目标
          AST 片段；不改变区域归约顺序与块归属。
        ③唯一归属判定：仅当汇合块内 `UNPACK_SEQUENCE/UNPACK_EX` 之后
          **紧邻**恰为 N 个 `STORE_FAST/NAME/GLOBAL/DEREF`（N = UNPACK 元素数）
          且其间无其它指令时成立；任一不满足返回 None，调用方维持既有单目标
          发射（C3 逐位回退）。
        ④嵌套处理：只处理本层 UNPACK 的元素（不展开嵌套解包，嵌套形仍走
          语句级既有 UNPACK 归约路径）。
        ⑤入口引用语义：不认领块、不登记 generated，只返回目标 AST。
        ⑥反编译流程：BoolOpRegion(value 上下文) → Assign(targets=[Tuple]).
        判据只读汇合块指令序列结构（opcode 与 UNPACK arg），不看名字、
        常量、偏移。
        """
        if region is None or getattr(region, 'merge_block', None) is None:
            return None
        _instrs = [i for i in region.merge_block.instructions
                   if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
        _fst = None
        for _idx, _i in enumerate(_instrs):
            if _i.opname in ('STORE_FAST', 'STORE_NAME',
                             'STORE_GLOBAL', 'STORE_DEREF',
                             'STORE_ATTR', 'STORE_SUBSCR'):
                _fst = _idx
                break
        if _fst is None or _fst < 1:
            return None
        _up_idx = _fst - 1
        _up = _instrs[_up_idx]
        if _up.opname not in ('UNPACK_SEQUENCE', 'UNPACK_EX'):
            return None
        _starred_at = -1
        if _up.opname == 'UNPACK_SEQUENCE':
            _n = _up.arg if _up.arg is not None else 0
        else:
            _arg = _up.argval if _up.argval is not None else _up.arg
            if _arg is None:
                return None
            _before = _arg & 0xFF
            _after = (_arg >> 8) & 0xFF
            if not _before and not _after:
                return None
            _n = _before + 1 + _after
            _starred_at = _before
        if _n < 2:
            return None
        _targets = []
        for _i in _instrs[_up_idx + 1:]:
            if _i.opname not in ('STORE_FAST', 'STORE_NAME',
                                 'STORE_GLOBAL', 'STORE_DEREF'):
                return None
            if len(_targets) == _starred_at:
                _targets.append({'type': 'Starred',
                                 'value': {'type': 'Name',
                                           'id': _i.argval, 'ctx': 'Store'}})
            else:
                _targets.append({'type': 'Name', 'id': _i.argval, 'ctx': 'Store'})
            if len(_targets) == _n:
                break
        if len(_targets) != _n:
            return None
        return {'type': 'Tuple', 'elts': _targets, 'ctx': 'Store'}

'''

INIT_ANCHOR = (
    "                    _full_rhs = boolop_expr\n"
    "                    _r64d4_solo = None\n"
)
INIT_PATCH = (
    "                    _full_rhs = boolop_expr\n"
    "                    _v164_unpack_tgt = None  # [v164-UNPACKTGT]\n"
    "                    _r64d4_solo = None\n"
)

PRESTORE_ANCHOR = "                            _pre_store = _mnn[:_si]\n"
PRESTORE_PATCH = (
    "                            _pre_store = _mnn[:_si]\n"
    "                            # [v164-UNPACKTGT] 汇合块含 UNPACK 时，元组目标\n"
    "                            # 由 Tuple 承载；UNPACK 指令不参与 rhs 表达式拼接。\n"
    "                            _v164_unpack_tgt = self._boolop_unpack_targets_at_join(region)\n"
    "                            if _v164_unpack_tgt is not None:\n"
    "                                _pre_store = [i for i in _pre_store\n"
    "                                              if i.opname not in ('UNPACK_SEQUENCE',\n"
    "                                                                  'UNPACK_EX')]\n"
)

ASSIGN_ANCHOR = '''                    else:
                        results.append({
                            'type': 'Assign',
                            'targets': [{'type': 'Name', 'id': region.value_target, 'ctx': 'Store'}],
                            'value': _full_rhs,
                        })
'''
ASSIGN_PATCH = '''                    else:
                        _v164_targets = [{'type': 'Name', 'id': region.value_target,
                                          'ctx': 'Store'}]
                        if _v164_unpack_tgt is not None:
                            _v164_targets = [_v164_unpack_tgt]
                        results.append({
                            'type': 'Assign',
                            'targets': _v164_targets,
                            'value': _full_rhs,
                        })
'''


def _read(path):
    raw = open(path, 'rb').read()
    nl = '\r\n' if b'\r\n' in raw else '\n'
    text = raw.decode('utf-8-sig').replace('\r\n', '\n').replace('\r', '\n')
    return text, nl


def _write(path, text, nl):
    if nl != '\n':
        text = text.replace('\n', nl)
    with open(path, 'wb') as f:
        f.write(b'\xef\xbb\xbf' + text.encode('utf-8'))


def apply_hunk(path, anchor, patch, marker):
    text, nl = _read(path)
    if marker in text:
        print('[fix164] %s: already applied' % os.path.basename(path))
        return 0
    n = text.count(anchor)
    if n != 1:
        print('[fix164] ERROR %s anchor count=%d (expected 1)'
              % (os.path.basename(path), n))
        return 2
    _write(path, text.replace(anchor, patch, 1), nl)
    print('[fix164] patched %s' % path)
    return 0


HELPER_FULL = HELPER + HELPER_ANCHOR


def main():
    rc = 0
    a_text, a_nl = _read(ANALYZER)
    if '# [v164-NOTMIXTAIL]' in a_text:
        print('[fix164] analyzer: already applied')
    else:
        n = a_text.count(ANCHOR_CHAIN)
        if n != 1:
            print('[fix164] ERROR analyzer anchor count=%d' % n)
            return 2
        _write(ANALYZER, a_text.replace(ANCHOR_CHAIN, PATCH_CHAIN, 1), a_nl)
        print('[fix164] patched %s' % ANALYZER)

    for anchor, patch, marker in (
            (HELPER_ANCHOR, HELPER_FULL, 'def _boolop_unpack_targets_at_join'),
            (INIT_ANCHOR, INIT_PATCH, '_v164_unpack_tgt = None'),
            (PRESTORE_ANCHOR, PRESTORE_PATCH, 'self._boolop_unpack_targets_at_join(region)'),
            (ASSIGN_ANCHOR, ASSIGN_PATCH, "'targets': _v164_targets")):
        rc = apply_hunk(GENERATOR, anchor, patch, marker)
        if rc:
            return rc

    py_compile.compile(ANALYZER, cfile=os.path.join(os.environ.get('TEMP', '.'),
                                                    '_fix164_a.pyc'), doraise=True)
    py_compile.compile(GENERATOR, cfile=os.path.join(os.environ.get('TEMP', '.'),
                                                     '_fix164_g.pyc'), doraise=True)
    print('[fix164] py_compile OK')
    return rc


if __name__ == '__main__':
    sys.exit(main())
