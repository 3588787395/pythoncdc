"""R21-42: let the landed [R41-B] arm-continue rule see CPython's continue re-entry block.

Measured chain (round 38, all numbers from `attrib_bytes.py`, which compares `co_code` byte-for-byte
per unit with jump operands included):

| configuration (`ipo_stocks_order` must stay at 0 bytes) | `ipo` | `_process_cancel_order` |
|---|---|---|
| landed generator + analyzer `f7d849e974904492` | 0 | 28 bytes (`else`-arm continue missing, `@1998 JUMP_BACKWARD`) |
| + 40c `ccd97ff680b7434c` (35a's Continue moved into the owning then-arm) | **0** | 28 bytes |
| + E1/E2 attempts on `[R8 fix]` / `[R39-B]` | 419 / 1 | 1 / 2 bytes |

`[R8 fix]` and `[R39-B]` are the wrong hosts: widening them buys the victim unit bytes but breaks
`ipo_stocks_order` (0 → 1 → 419). The right host is already in the file and was written for precisely
this shape — `[R41-B]` at `region_ast_generator.py:26819-26852`: "a CONTINUE-role block that carries
user statements must emit an explicit `Continue` unless its back edge is the loop's natural one". Its
conjunct ① is

    and self.cfg.get_block_by_offset(_r41b_last.argval) is _r41b_hdr

i.e. it accepts only a back edge landing on `header_block`. Measured fact from this unit's CFG: CPython
3.11 compiles an *explicit* `continue` onto the loop's **pure-noise re-entry block** (`@44` = one NOP,
single successor `@46` = the header) and reserves the header landing for the implicit body tail. So the
very case `[R41-B]` exists to cover — `else: strategy_log.error(_('当前订单状态不支持撤单')); continue`,
whose block is `@1930..@1998` ending in `JUMP_BACKWARD -> @44` — is excluded by its own ①, and the
`Continue` is dropped.

Fix: accept a landing that is either the header (unchanged behaviour) or the continue re-entry block,
recognized by the same structural predicate this file already uses elsewhere and in the [R21-40]
analyzer hunk: a block before the header, containing no user instruction, with exactly one successor
which is the header. Nothing else in `[R41-B]` moves (② merge-block-not-header and ③ not-the-arm's-last-block
keep their guarding roles), so the change is monotone: it can only ADD the `Continue` the rule was
written to add, in the landing shape it used to miss.

usage: python -X utf8 build_cand_r38_R21-42_r41b_reentry.py     # writes CAND_r42_gen.py
"""
import hashlib
import py_compile

SRC = 'D:/Temp/r38/CAND_r40c_gen.py'
OUT = 'D:/Temp/r40/CAND_r42_gen.py'

OLD_PRE = [
    "                    _r41b_hdr = (getattr(self._current_loop, 'header_block', None)",
    "                                 if self._current_loop else None)",
    "                    _r41b_last = block.get_last_instruction()",
    "                    _r41b_pos = next((_i for _i, _b in enumerate(blocks) if _b is block), -1)",
]

NEW_PRE = [
    "                    _r41b_hdr = (getattr(self._current_loop, 'header_block', None)",
    "                                 if self._current_loop else None)",
    "                    _r41b_last = block.get_last_instruction()",
    "                    _r41b_pos = next((_i for _i, _b in enumerate(blocks) if _b is block), -1)",
    "                    # [R21-42] ①的落点判定补上 CPython 的 continue 再入块：显式 continue 跳的是 header 之前",
    "                    # 那条纯噪声、唯一后继即 header 的 NOP（本单元实测 @44，header=@46），隐式体尾才直接跳",
    "                    # header。原判据只认后者，于是 `else: error(...); continue` 这种「带语句的 CONTINUE 角色",
    "                    # 块」被自己的 ① 挡掉，显式 Continue 整条丢失（@1998 的 JUMP_BACKWARD 即此）。",
    "                    # 识别用的是本文件与 [R21-40] 分析层同一结构事实，不读名字/偏移/指令计数。",
    "                    _r41b_land = None",
    "                    _r41b_reentry = False",
    "                    if (_r41b_last is not None",
    "                            and _r41b_last.opname in ('JUMP_BACKWARD',",
    "                                                      'JUMP_BACKWARD_NO_INTERRUPT')",
    "                            and _r41b_last.argval is not None and _r41b_hdr is not None):",
    "                        _r41b_land = self.cfg.get_block_by_offset(_r41b_last.argval)",
    "                        _r41b_reentry = (_r41b_land is not None",
    "                                         and _r41b_land is not _r41b_hdr",
    "                                         and getattr(_r41b_land, 'instructions', None)",
    "                                         and _r41b_land.start_offset < _r41b_hdr.start_offset",
    "                                         and all(i.opname in ('RESUME', 'NOP', 'CACHE',",
    "                                                      'PUSH_NULL', 'EXTENDED_ARG',",
    "                                                      'END_ASYNC_FOR')",
    "                                                  for i in _r41b_land.instructions)",
    "                                         and len(_r41b_land.successors) == 1",
    "                                         and _r41b_hdr in _r41b_land.successors)",
]

OLD_CONJ = [
    "                            and self.cfg.get_block_by_offset(_r41b_last.argval) is _r41b_hdr",
]
NEW_CONJ = [
    "                            and (_r41b_land is _r41b_hdr or _r41b_reentry)",
]


def sha16(b):
    return hashlib.sha256(b).hexdigest()[:16]


def splice(lines, old, new, tag):
    hits = [n for n in range(len(lines) - len(old) + 1) if lines[n:n + len(old)] == old]
    assert len(hits) == 1, '%s: anchor hits %d' % (tag, len(hits))
    n = hits[0]
    return lines[:n] + new + lines[n + len(old):]


def main():
    raw = open(SRC, 'rb').read()
    assert raw.startswith(b'\xef\xbb\xbf') and raw.count(b'\n') == raw.count(b'\r\n')
    lines = [x.encode('utf-8') for x in OLD_PRE]
    o = raw.split(b'\r\n')
    o = splice(o, [x.encode('utf-8') for x in OLD_PRE], [x.encode('utf-8') for x in NEW_PRE], 'pre')
    o = splice(o, [x.encode('utf-8') for x in OLD_CONJ], [x.encode('utf-8') for x in NEW_CONJ], 'conjunct')
    data = b'\r\n'.join(o)
    open(OUT, 'wb').write(data)
    py_compile.compile(OUT, doraise=True)
    print('42 sha16=%s size=%d (base %s) py_compile=OK' % (sha16(data), len(data), sha16(raw)))


if __name__ == '__main__':
    main()
