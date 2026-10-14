# -*- coding: utf-8 -*-
"""build_r95.py — regenerate the R21-66 candidate generator from the LANDED bytes byte-exactly.

Usage: python -X utf8 build_r95.py            (idempotent: always starts from LANDED_SRC)

Discipline: UTF-8 BOM kept, all-CRLF only, patch by split(b'\\r\\n'), every anchor asserted unique,
never re-encode the whole file by hand, assert b'\\r\\r\\n' count == 0, py_compile after the write.
"""
import hashlib
import os
import py_compile
import shutil
import sys

LANDED = 'D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main/core/cfg/region_ast_generator.py'
MIRROR = 'D:/Temp/r95/core/cfg/region_ast_generator.py'
SEED = 'D:/Temp/r95/seed/region_ast_generator_LANDED_b4363f5858e58074.py'
EXPECT_LANDED16 = 'b4363f5858e58074'

BOM = b'\xef\xbb\xbf'


def sha16(b):
    return hashlib.sha256(b).hexdigest()[:16]


# ---------------------------------------------------------------- anchor helpers
def lines_of(data):
    body = data[len(BOM):] if data.startswith(BOM) else data
    return body.split(b'\r\n')


def encode(lines):
    return BOM + b'\r\n'.join(lines)


def find_unique(lines, anchor_lines, what):
    idxs = []
    n = len(anchor_lines)
    for i in range(len(lines) - n + 1):
        if lines[i:i + n] == anchor_lines:
            idxs.append(i)
    if len(idxs) != 1:
        raise SystemExit('[anchor not unique] %s -> %d occurrences' % (what, len(idxs)))
    return idxs[0]


def T(*s):
    return [x.encode('utf-8') for x in s]


# ---------------------------------------------------------------- Hunk 1: SEG builder
H1_ANCHOR = T(
    "                    self.generated_blocks.add(cond_block)",
    "                    self.generated_offsets.add(cond_block.start_offset)",
)
H1_NEW = T(
    '                    # [R21-66 闩锁副本身份集] CPython 3.11 把 while 条件求值在回边处',
    '                    # 逐字复制一份（模板 `while a or b or c:`：入口副本腿前跳 body 首块，',
    '                    # 闩锁副本腿后跳同一块）。故「本 body 块的尾巴是不是条件副本」只能',
    '                    # 用**操作码名序列等值**判定：SEG = 本循环自己每一段条件求值',
    '                    # （condition_block + condition_chain_blocks）去掉噪声指令与末条条件',
    '                    # 跳转后的 opcode 名序列。EXTENDED_ARG 是跳转距离前缀（噪声），两端',
    '                    # 一并剔除后比较。纯块内数据，无函数名/文件名/绝对偏移/计数阈值。',
    '                    _r2166_seg_set = set()',
    '                    for _r2166_seg_blk in [cond_block] + list(_cc_chain):',
    '                        _r2166_seg_ins = [i for i in _r2166_seg_blk.instructions',
    '                                          if i.opname not in (',
    '                                              \'RESUME\', \'NOP\', \'CACHE\', \'PUSH_NULL\',',
    '                                              \'EXTENDED_ARG\')]',
    '                        _r2166_seg_last = _r2166_seg_blk.get_last_instruction()',
    '                        if (_r2166_seg_last is not None',
    '                                and _r2166_seg_last.opname in CONDITIONAL_JUMP_OPS',
    '                                and _r2166_seg_ins',
    '                                and _r2166_seg_ins[-1] is _r2166_seg_last):',
    '                            _r2166_seg_ins = _r2166_seg_ins[:-1]',
    '                        if _r2166_seg_ins:',
    '                            _r2166_seg_set.add(tuple(i.opname for i in _r2166_seg_ins))',
)

# ---------------------------------------------------------------- Hunk 2: boundary + copy test
H2_ANCHOR = T(
    "                        _last_store_idx = -1",
    "                        for _si, _i in enumerate(_b_non_jmp):",
    "                            if _i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):",
    "                                _last_store_idx = _si",
    "                        if _last_store_idx >= 0:",
    "                            _post_store = _b_non_jmp[_last_store_idx + 1:]",
    "                            _is_recheck = any(i.opname in ('COPY', 'COMPARE_OP', 'IS_OP', 'CONTAINS_OP')",
    "                                              for i in _post_store)",
    "                            if _is_recheck:",
)
H2_NEW = T(
    "                        _last_store_idx = -1",
    "                        # [R21-66 语句边界] STORE_* 与 POP_TOP 都是语句终结符：CPython 会把",
    "                        # 闩锁副本融合在前一条语句之后，前缀既可能是赋值（`x += 1`），也可能是",
    "                        # 纯表达式语句（`f()` 以 POP_TOP 丢弃结果）。边界集因此取两者并集。",
    "                        _r2166_bnd_idx = -1",
    "                        for _si, _i in enumerate(_b_non_jmp):",
    "                            if _i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):",
    "                                _last_store_idx = _si",
    "                                _r2166_bnd_idx = _si",
    "                            elif _i.opname == 'POP_TOP':",
    "                                _r2166_bnd_idx = _si",
    "                        # [R21-66 副本判据] 最后一条语句边界之后的求值尾段，逐字等于本循环",
    "                        # 条件的一段，才是 CPython 复制的 while 测试。**旧判据「尾部含",
    "                        # COMPARE_OP」不是副本判据**：`s = e()` 后随 `if s > k:` 的普通语句块",
    "                        # 同样含 COMPARE_OP，旧代码因此把整块抑制、把 store 追加到循环体末尾、",
    "                        # 并把该 if 的 then 块降级为无条件语句（实测 _sync_worker 第二循环 @2214",
    "                        # 尾巴 [LOAD_FAST, LOAD_GLOBAL, COMPARE_OP] != SEG=[16 段, 5 段]）。",
    "                        _r2166_tail = (_b_non_jmp[_r2166_bnd_idx + 1:]",
    "                                       if _r2166_bnd_idx >= 0 else [])",
    "                        _r2166_is_latch_copy = bool(_r2166_tail) and (",
    "                            tuple(i.opname for i in _r2166_tail",
    "                                  if i.opname != 'EXTENDED_ARG') in _r2166_seg_set)",
    "                        # [R21-66 闩锁终点] 副本沿链的终点必须是循环自己：本块后继里出现",
    "                        # back_edge_block（链的下一段所在块）或 header_block（重入测试块）。",
    "                        # 前后继关系判据，不看偏移、不看名字。",
    "                        _r2166_succ = list(_b.successors or [])",
    "                        _r2166_latch_end = (region.back_edge_block is not None",
    "                                            and region.back_edge_block in _r2166_succ) \\",
    "                            or (region.header_block is not None",
    "                                and region.header_block in _r2166_succ)",
    "                        if _last_store_idx >= 0:",
    "                            _post_store = _b_non_jmp[_last_store_idx + 1:]",
    "                            _is_recheck = any(i.opname in ('COPY', 'COMPARE_OP', 'IS_OP', 'CONTAINS_OP')",
    "                                              for i in _post_store)",
    "                            # [R21-66] 收紧：仅在尾段确为本循环条件副本时提取 store。",
    "                            # 边界必须是最后一条 STORE（否则前缀里含表达式语句，交给下面",
    "                            # 的 case A 分支重建），保持旧路径对其原有命中形态逐字节不变。",
    "                            if _is_recheck and _r2166_is_latch_copy \\",
    "                                    and _r2166_bnd_idx == _last_store_idx:",
)

# ---------------------------------------------------------------- Hunk 3: case A + case C
H3_ANCHOR = T(
    "                        # Pure recheck: back_edge block with only COMPARE_OP + jump",
    "                        if _b is region.back_edge_block:",
    "                            _has_only_compare = all(",
    "                                i.opname in ('LOAD_CONST', 'LOAD_FAST', 'LOAD_NAME',",
    "                                             'LOAD_GLOBAL', 'LOAD_DEREF', 'COPY', 'SWAP',",
    "                                             'COMPARE_OP', 'IS_OP', 'CONTAINS_OP', 'POP_TOP')",
    "                                for i in _b_non_jmp)",
    "                            if _has_only_compare:",
    "                                self.generated_blocks.add(_b)",
    "                                self.generated_offsets.add(_b.start_offset)",
    "                                continue",
)
H3_NEW = T(
    "                        # [R21-66 case A] 前缀是 POP_TOP 结束的表达式语句 + 闩锁副本尾段：",
    "                        # 提取语句为循环体语句（同既有 recheck_store_stmts 通道，位置在该块",
    "                        # 语句流原位——闩锁块按构造是循环体的最后一条语句块），整块标记已生成，",
    "                        # 副本本身归约掉（它由 while 条件语义承担，不得再打印）。",
    "                        # 判据（opcode 类 + 区域数据 + 前后继关系，无名字/偏移/阈值）：",
    "                        #   (1) 块尾是条件跳转（上方 :8130 已判）；",
    "                        #   (2) 块内无 STORE，最后语句边界是 POP_TOP（表达式语句）；",
    "                        #   (3) 边界后的尾段 == SEG 中某段（条件副本身份）；",
    "                        #   (4) 该块的后继含本循环的 back_edge_block 或 header_block，即副本",
    "                        #       沿链继续、终点是循环自身（闩锁），不是分支出口；",
    "                        #   (5) 本块不是循环 header_block（header 的副本尾巴由上面的 store",
    "                        #       通道处理，此处不接管，避免改动既有已验证形态）。",
    "                        # 语句重建只走既有三级重建 `_build_store_statement` → `_build_statement`；",
    "                        # 重建失败则整条规则不生效（不回改、不静默丢语句）。",
    "                        if (_r2166_is_latch_copy and _last_store_idx < 0",
    "                                and _r2166_bnd_idx >= 0",
    "                                and _b_non_jmp[_r2166_bnd_idx].opname == 'POP_TOP'",
    "                                and _b is not region.header_block",
    "                                and _r2166_latch_end):",
    "                            _r216a_stmt_instrs = _b_non_jmp[:_r2166_bnd_idx + 1]",
    "                            _r216a_stmt = self._build_store_statement(",
    "                                _r216a_stmt_instrs, block=_b) or self._build_statement(",
    "                                _r216a_stmt_instrs)",
    "                            if _r216a_stmt:",
    "                                _r216a_stmt.pop('_decorator_block', None)",
    "                                recheck_store_stmts.append(_r216a_stmt)",
    "                                self.generated_blocks.add(_b)",
    "                                self.generated_offsets.add(_b.start_offset)",
    "                                continue",
    "                        # Pure recheck: back_edge block with only COMPARE_OP + jump",
    "                        if _b is region.back_edge_block:",
    "                            _has_only_compare = all(",
    "                                i.opname in ('LOAD_CONST', 'LOAD_FAST', 'LOAD_NAME',",
    "                                             'LOAD_GLOBAL', 'LOAD_DEREF', 'COPY', 'SWAP',",
    "                                             'COMPARE_OP', 'IS_OP', 'CONTAINS_OP', 'POP_TOP')",
    "                                for i in _b_non_jmp)",
    "                            # [R21-66 case C] 白名单只收 LOAD/COPY/SWAP/COMPARE 类，条件副本里",
    "                            # `int(x)` 这类带 CALL 载荷的操作数被白名单否决（实测 _sync_worker",
    "                            # 第二循环 back_edge @2844 = [LOAD_GLOBAL, LOAD_FAST, PRECALL, CALL,",
    "                            # COMPARE_OP] == SEG 的 chain 段）。补一条身份判据：整块非跳转序列逐字",
    "                            # 等于本循环条件的一段 ⇒ 它就是被复制的测试，纯重检，整块抑制。",
    "                            _r2166_pure_copy = bool(_b_non_jmp) and (",
    "                                tuple(i.opname for i in _b_non_jmp",
    "                                      if i.opname != 'EXTENDED_ARG') in _r2166_seg_set)",
    "                            if _has_only_compare or _r2166_pure_copy:",
    "                                self.generated_blocks.add(_b)",
    "                                self.generated_offsets.add(_b.start_offset)",
    "                                continue",
)


def main():
    landed = open(LANDED, 'rb').read()
    assert sha16(landed) == EXPECT_LANDED16, sha16(landed)
    if not os.path.isdir(os.path.dirname(SEED)):
        os.makedirs(os.path.dirname(SEED))
    if not os.path.isfile(SEED):
        shutil.copyfile(LANDED, SEED)
    assert open(SEED, 'rb').read() == landed, 'seed drift'

    lines = lines_of(landed)
    for i, ln in enumerate(lines):
        if b'\r' in ln:
            raise SystemExit('[bad line] bare CR at index %d' % i)

    i1 = find_unique(lines, H1_ANCHOR, 'H1')
    lines[i1 + len(H1_ANCHOR):i1 + len(H1_ANCHOR)] = H1_NEW
    i2 = find_unique(lines, H2_ANCHOR, 'H2')
    lines[i2:i2 + len(H2_ANCHOR)] = H2_NEW
    i3 = find_unique(lines, H3_ANCHOR, 'H3')
    lines[i3:i3 + len(H3_ANCHOR)] = H3_NEW

    out = encode(lines)
    assert out.count(b'\r\r\n') == 0
    assert b'\n' not in out.replace(b'\r\n', b'')
    open(MIRROR, 'wb').write(out)
    py_compile.compile(MIRROR, doraise=True)
    print('candidate written bytes=%d sha16=%s (landed %s)'
          % (len(out), sha16(out), sha16(landed)))


if __name__ == '__main__':
    sys.exit(main())
