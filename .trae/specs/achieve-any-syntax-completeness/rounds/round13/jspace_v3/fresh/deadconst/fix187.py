# -*- coding: utf-8 -*-
"""rr-v5r187 patch: 推导式过滤位「折叠臂死常量」发射族
（T2 = 折叠臂常量取池残留对象；T1 = 折叠真值 orelse 走 IfExp 形）。

用法（cwd 任意；默认仓库根 F:\\Downloads\\pythoncdc-main）:
    D:/Python/python.exe -I -X utf8 fix187.py            # 应用补丁（幂等）
    D:/Python/python.exe -I -X utf8 fix187.py --revert   # 回退（往返 sha 一致）

约束（rules.md）:
  §1.4 I.4 白名单：新增判据只读本 code object 的常量表 / 同层 LOAD_CONST 操作数 /
        块末 opcode 与跳转 argval / 块起点偏移；不读文件名、用户名、J 标签、偏移阈值。
  §2.1：新增符号 `_fold_arm_value`、`_pool_dead_bool`、`_try_folded_true_arm`
        均无禁用前缀（_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_）。
  §2.2：无硬编码深度/计数上限；池扫描与块遍历的终止性由常量表长度/块集有限性保证。
  编码：comprehension_generator.py 为「无 BOM + CRLF」，补丁逐字节保持原行尾；
        region 两文件本轮不改动，其 BOM 单头不受影响。
  锚点：每个 hunk 的 old 文本在目标文件中必须恰好出现 1 次（count==1）。
"""
from __future__ import annotations

import hashlib
import os
import py_compile
import sys
import tempfile

REPO = os.environ.get('R187_REPO') or r'F:\Downloads\pythoncdc-main'
CG = os.path.join(REPO, 'core', 'cfg', 'comprehension_generator.py')

# ---------------------------------------------------------------- hunk 1
# 签名：把 code object 传进过滤器解析器（常量池 = 折叠臂常量的唯一残留 oracle）
H1_OLD = '''    def _b256_filter_boolchain(self, all_instrs: List[Instruction],
                               store_idx: int, append_idx: int,
                               value_count: int = 1
                               ) -> Optional[Tuple[Dict[str, Any], int,
                                                   List[Dict[str, Any]]]]:
'''

H1_NEW = '''    def _b256_filter_boolchain(self, all_instrs: List[Instruction],
                               store_idx: int, append_idx: int,
                               value_count: int = 1,
                               code_obj: Any = None
                               ) -> Optional[Tuple[Dict[str, Any], int,
                                                   List[Dict[str, Any]]]]:
'''

# ---------------------------------------------------------------- hunk 2
# 常量池残留判据 + 折叠臂常量取值（插在 `_is_jump` 之前）
H2_OLD = '''        _UNCOND = ('JUMP_FORWARD', 'JUMP_ABSOLUTE', 'JUMP_BACKWARD',
                   'JUMP_BACKWARD_NO_INTERRUPT')

        def _is_jump(_i: Instruction) -> bool:
'''

H2_NEW = '''        _UNCOND = ('JUMP_FORWARD', 'JUMP_ABSOLUTE', 'JUMP_BACKWARD',
                   'JUMP_BACKWARD_NO_INTERRUPT')

        # [R187-DEADARM] 折叠臂常量的常量池残留判据。
        # CPython 3.11 把过滤位被编译期折叠的臂常量**登记进 co_consts**，但
        # `compiler_jump_if` 只发射跳转、不发射该值（没有 LOAD_CONST 引用 =
        # 死常量）。实测：`[x for x in xs if (x if b else 0)]` 的 <listcomp>
        # 池 `(0,)`、`co_code` 里 0 条 LOAD_CONST；同一 `co_code` 的合成形态
        # `else False` 的池是 `(False,)`（逐字节相同的指令流）。故折叠臂的
        # 常量对象只能由池残留给出：池里已登记该真值的 bool ⇒ 发该 bool（与
        # 既有行为恒等）；池里没有该 bool 而有同真值的死 int 项 ⇒ 发该项
        # （0/1）。判据只读本 code object 的常量表与同层 LOAD_CONST/KW_NAMES
        # 操作数（I.4 白名单），无值特判、无偏移/计数上限。
        _pool = tuple(getattr(code_obj, 'co_consts', ()) or ())
        _pool_loaded = set()
        for _ins in all_instrs:
            if _ins.opname in ('LOAD_CONST', 'RETURN_CONST', 'KW_NAMES'):
                if isinstance(_ins.arg, int):
                    _pool_loaded.add(_ins.arg)
        _pool_dead = [(i, c) for i, c in enumerate(_pool)
                      if i not in _pool_loaded]

        def _fold_arm_value(_truth: bool):
            """折叠臂常量：池里已登记该真值的 bool 就发它，否则发同真值死 int 项。"""
            if any(type(_c) is bool and _c == _truth for _c in _pool):
                return {'type': 'Constant', 'value': _truth}
            for _, _c in _pool_dead:
                if type(_c) is int and _c == _truth:
                    return {'type': 'Constant', 'value': _c}
            return {'type': 'Constant', 'value': _truth}

        def _pool_dead_bool(_truth: bool) -> bool:
            """池里是否存在未被任何指令引用的 bool 对象 `_truth`（折叠真值臂痕迹）。"""
            return any(type(_c) is bool and _c is _truth for _, _c in _pool_dead)

        def _is_jump(_i: Instruction) -> bool:
'''

# ---------------------------------------------------------------- hunk 3
# `_arm_const`：裸无条件跳转的折叠臂
H3_OLD = '''            return ({'type': 'Constant',
                     'value': False if _j.argval == _next_off else True},
                    frozenset([_j.argval]))
'''

H3_NEW = '''            return (_fold_arm_value(_j.argval != _next_off),
                    frozenset([_j.argval]))
'''

# ---------------------------------------------------------------- hunk 4
# `_try_ifexp`：两臂均折叠为空的三元（两臂各发一个真值常量）
H4_OLD = '''                        _zarm = {'type': 'Constant', 'value': True}
'''

H4_NEW = '''                        _zarm = _fold_arm_value(True)
'''

# ---------------------------------------------------------------- hunk 5
# `_parse_impl`：空段（零指令臂）
H5_OLD = '''            if _i == _end:
                return ({'type': 'Constant', 'value': True if _cond == 0 else False},
                        frozenset())
'''

H5_NEW = '''            if _i == _end:
                return (_fold_arm_value(_cond == 0), frozenset())
'''

# ---------------------------------------------------------------- hunk 6
# `_parse_impl`：单块无条件跳转 = 折叠的常量臂
H6_OLD = '''                        return ({'type': 'Constant',
                                 'value': False if _cond == 0 else True},
                                frozenset([_last.argval]))
'''

H6_NEW = '''                        return (_fold_arm_value(_cond != 0),
                                frozenset([_last.argval]))
'''

# ---------------------------------------------------------------- hunk 7
# 新增「折叠真值 orelse」三元通道（插在 `_parse` 记忆化包装之前）
H7_OLD = '''            return None

        def _parse(_i: int, _end: int, _next_off: Optional[int],
                   _cond: int) -> Optional[Tuple[Dict[str, Any], frozenset]]:
'''

H7_NEW = '''            return None

        def _try_folded_true_arm(_i: int, _end: int,
                                 _next_off: Optional[int], _cond: int
                                 ) -> Optional[Tuple[Dict[str, Any],
                                                     frozenset]]:
            """[R187-FOLDTRUE] 过滤位「折叠真值 orelse」三元。

            ①算法依据（CPython 3.11 `compiler_jump_if` 的 IfExp 分支）：test 按
              `(next2, 0)` 递归，两臂各按 `(next, cond)` 递归；orelse 是常量真值
              时该臂零指令，`next2` 块的偏移就是通过点（元素起点）。真臂若以
              filter 回跳（BACKWARD IF_FALSE → 跳过本轮）收尾，整窗只剩两条跳
              转：test 块末的 FORWARD IF_FALSE 落在通过点、真臂块末的 BACKWARD
              IF_FALSE 落在 `_next_off`。
            ②归约方式：真臂整段交 `_leaf_value`（既有重建器黑箱，末条回跳剥除），
              test 单独交 `_leaf_value`，orelse 交 `_fold_arm_value(True)`。
            ③唯一归属判定（池残留当 oracle）：本形只在池里存在**未被引用**的
              bool `True` 时成立——该死常量是原件发过真值常量臂的唯一指令侧
              痕迹（`not flag or x % 2` 这类 De Morgan 形态不会 intern `True`；
              元素位 `else True` 会发 `LOAD_CONST True` 而成为活常量）。池里没有
              死 `True` 时维持 `_try_boolop` 的 De Morgan 形态，文本逐字节不变。
            ④AST 映射：IfExp(test, body=真臂, orelse=True) 在 filter 位重编译回
              同一跳转流（真值常量 orelse 零指令，[C1] 编译器结构保证），池里
              `True` 的登记位置随之复现。
            [C1] 只读同层块末 opcode/argval、块起点偏移与本 code object 常量表；
            [C2] 两段表达式整体交既有重建器黑箱；[C3] 极性（非 FORWARD IF_FALSE）、
            落点（test 不经通过点 / 真臂不回跳过本轮）任一不符即返回 None，调用
            方沿用既有通道。
            """
            if _cond != 0 or _next_off is None or _end - _i < 2:
                return None
            if not _pool_dead_bool(True):
                return None
            _lt = all_instrs[_blocks[_i][1] - 1]
            if ('IF_FALSE' not in _lt.opname
                    or 'BACKWARD' in _lt.opname
                    or _lt.argval != _blk_off(_end)):
                return None
            _la = all_instrs[_blocks[_end - 1][1] - 1]
            if ('IF_FALSE' not in _la.opname
                    or 'BACKWARD' not in _la.opname
                    or _la.argval != _next_off):
                return None
            _test = _leaf_value(_i, _i + 1)
            _arm = _leaf_value(_i + 1, _end)
            if _test is None or _arm is None:
                return None
            return ({'type': 'IfExp', 'test': _test, 'body': _arm,
                     'orelse': _fold_arm_value(True)},
                    frozenset([_next_off]))

        def _parse(_i: int, _end: int, _next_off: Optional[int],
                   _cond: int) -> Optional[Tuple[Dict[str, Any], frozenset]]:
'''

# ---------------------------------------------------------------- hunk 8
# 接线：BoolOp 通道之前先试折叠真值臂通道
H8_OLD = '''            _r = _try_boolop(_i, _end, _next_off, _cond)
'''

H8_NEW = '''            _fo = _try_folded_true_arm(_i, _end, _next_off, _cond)
            if _fo is not None:
                return _fo
            _r = _try_boolop(_i, _end, _next_off, _cond)
'''

# ---------------------------------------------------------------- hunk 9
# 单 for 路径：调用过滤器解析器时提供本 code object
H9_OLD = '''        _ternary_filter_info = self._b256_filter_boolchain(
            all_instrs, store_idx, append_idx,
            2 if append_op == 'MAP_ADD' else 1)
'''

H9_NEW = '''        _ternary_filter_info = self._b256_filter_boolchain(
            all_instrs, store_idx, append_idx,
            2 if append_op == 'MAP_ADD' else 1, code_obj=code_obj)
'''

# ---------------------------------------------------------------- hunk 10
# 多 for 路径：同上
H10_OLD = '''        _ternary_filter_info = self._b256_filter_boolchain(
            all_instrs, innermost_store_idx, append_idx,
            2 if append_op == 'MAP_ADD' else 1)
'''

H10_NEW = '''        _ternary_filter_info = self._b256_filter_boolchain(
            all_instrs, innermost_store_idx, append_idx,
            2 if append_op == 'MAP_ADD' else 1, code_obj=code_obj)
'''

PATCHES = [
    (CG, H1_OLD, H1_NEW, 'hunk1 pool-aware signature',
     'value_count: int = 1,\n                               code_obj: Any = None'),
    (CG, H2_OLD, H2_NEW, 'hunk2 dead-arm pool helpers',
     'def _fold_arm_value(_truth: bool):'),
    (CG, H3_OLD, H3_NEW, 'hunk3 arm_const pool value',
     'return (_fold_arm_value(_j.argval != _next_off),'),
    (CG, H4_OLD, H4_NEW, 'hunk4 ifexp folded arm value',
     '_zarm = _fold_arm_value(True)'),
    (CG, H5_OLD, H5_NEW, 'hunk5 empty segment pool value',
     'return (_fold_arm_value(_cond == 0), frozenset())'),
    (CG, H6_OLD, H6_NEW, 'hunk6 bare-jump arm pool value',
     'return (_fold_arm_value(_cond != 0),'),
    (CG, H7_OLD, H7_NEW, 'hunk7 folded true-orelse channel',
     'def _try_folded_true_arm(_i: int, _end: int,'),
    (CG, H8_OLD, H8_NEW, 'hunk8 wire folded true-orelse channel',
     '_fo = _try_folded_true_arm(_i, _end, _next_off, _cond)'),
    (CG, H9_OLD, H9_NEW, 'hunk9 single-for call site',
     "2 if append_op == 'MAP_ADD' else 1, code_obj=code_obj)"),
    (CG, H10_OLD, H10_NEW, 'hunk10 multi-for call site',
     'innermost_store_idx, append_idx,\n            2 if append_op == '
     "'MAP_ADD' else 1, code_obj=code_obj)"),
]


def sha256(path):
    with open(path, 'rb') as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def read_text(path):
    raw = open(path, 'rb').read()
    has_bom = raw.startswith(b'\xef\xbb\xbf')
    text = raw.decode('utf-8-sig')
    crlf = raw.count(b'\r\n') * 2 >= max(1, text.count('\n'))
    text = text.replace('\r\n', '\n')
    return text, has_bom, crlf


def write_text(path, text, has_bom, crlf, eol='\n'):
    data = text.replace('\r\n', '\n')
    if crlf:
        data = data.replace('\n', '\r\n')
    blob = data.encode('utf-8')
    if has_bom:
        blob = b'\xef\xbb\xbf' + blob
    with open(path, 'wb') as fh:
        fh.write(blob)


def apply(direction):
    """direction='apply' 用 old→new；'revert' 用 new→old。

    状态判据用各 hunk 的 marker（新文本独有片段），保证幂等与可逆：
      apply  : marker 已在 ⇒ 跳过；否则 old 必须恰好出现 1 次（count==1）；
      revert : marker 不在 ⇒ 跳过；否则 new 必须恰好出现 1 次。
    （插入式 hunk 的 new 文本包含 old 文本，故不能用 count(old) 判状态。）
    """
    text, has_bom, crlf = read_text(CG)
    upstream = text
    for path, old, new, tag, marker in PATCHES:
        src, dst = (old, new) if direction == 'apply' else (new, old)
        applied = marker in upstream
        if (direction == 'apply' and applied) or (direction == 'revert' and not applied):
            print('[skip] %-44s already %sd'
                  % (tag, 'applied' if direction == 'apply' else 'reverted'))
            continue
        n = upstream.count(src)
        if n != 1:
            raise SystemExit('[fatal] %s: anchor count=%d for %s (%s)'
                             % (path, n, tag, direction))
        upstream = upstream.replace(src, dst, 1)
        print('[%-6s] %-40s %s' % (direction, tag, os.path.basename(path)))
    if upstream == text:
        print('[noop] nothing to change')
        return 0
    before = sha256(CG)
    write_text(CG, upstream, has_bom, crlf)
    tmpdir = tempfile.mkdtemp(prefix='fix187_')
    try:
        py_compile.compile(CG, cfile=os.path.join(tmpdir, 'x.pyc'), doraise=True)
    except py_compile.PyCompileError as exc:
        print('[fatal] py_compile failed: %s' % exc)
        write_text(CG, text, has_bom, crlf)
        print('[rollback] restored original bytes')
        return 1
    print('  %-46s sha256 %s -> %s'
          % (os.path.relpath(CG, REPO), before[:16], sha256(CG)[:16]))
    raw = open(CG, 'rb').read()
    if has_bom:
        assert raw.startswith(b'\xef\xbb\xbf'), 'BOM lost in %s' % CG
        assert raw.count(b'\xef\xbb\xbf') == 1, 'duplicated BOM in %s' % CG
    else:
        assert not raw.startswith(b'\xef\xbb\xbf'), 'unexpected BOM in %s' % CG
    if crlf:
        assert b'\r\n' in raw and raw.count(b'\r\n') * 2 >= raw.count(b'\n')
    print('[ok] %s done' % direction)
    return 0


def main(argv):
    if '--revert' in argv:
        return apply('revert')
    return apply('apply')


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
