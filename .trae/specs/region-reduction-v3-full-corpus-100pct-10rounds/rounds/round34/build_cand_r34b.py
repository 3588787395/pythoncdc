"""R34 candidate v2: three own-data conjuncts on the P1-3b Continue suppression.

v1 (interior-only, `724f1843f9522fec`) was MEASURED and FALSIFIED on the 20-file panel:
broker 122->123 (+1 flip, ipo_stocks_order) but quote 91->90 and real_quote 45->44,
i.e. net -1 units. The two damages are blocks that CARRY STATEMENTS before their
back-edge (quote.one_prod_to_dataframe @1818 = `index.append(temp_time)` + jump), where
adding a `continue` turns the reachable statements after it into dead code (-14 instrs).

v2 therefore denies suppression only to a block that has NONE of the three facts that
make a recompiled loop regenerate the back-edge itself:
  1. it is not the enclosing LoopRegion's declared back_edge_block / in back_edge_blocks,
  2. it is not the body's terminal block in offset order,
  3. it carries no statement payload (EXTENDED_ARG is an operand-width prefix, not a
     statement - the victim block is exactly [EXTENDED_ARG, JUMP_BACKWARD]).
Corpus population (census_r34_loop_tail.py): 543 convergence hits, 479 terminal,
64 interior, 41 interior-payload-free, 24 satisfying all three (controls: victim @3572
in; quote @1818 / real_quote @1464 / handlers._target @200 out).

usage: python -X utf8 build_cand_r34b.py <generator-file>   (idempotence: refuses a
patched file by asserting the pristine 4-line tail is present exactly once)
"""
import hashlib
import py_compile
import sys

NEW = [
    "        # [R21-28] 回边块的收尾资格：本 LoopRegion 自己声明的回边块、或体内最高偏移的",
    "        # 收尾块、或本身带语句载荷（语句照常发射，回边由循环结构重编译再生）时才抑制",
    "        # 显式 Continue。三者皆无 => 本块是源码 continue 的专属块，抑制会少发一条",
    "        # JUMP_BACKWARD（ipo_stocks_order @3572 = [EXTENDED_ARG, JUMP_BACKWARD]，非声明",
    "        # 回边、体内到 @6194 仍有语句；反例 quote.one_prod_to_dataframe @1818 带语句载荷，",
    "        # 补发 continue 会把它之后 14 条可达语句变成死码，实测 91/92->90/92）。",
    "        _lc_payload = [i for i in block.instructions",
    "                       if i.opname not in ('RESUME', 'NOP', 'CACHE', 'EXTENDED_ARG',",
    "                                           'PUSH_NULL', 'POP_TOP', 'JUMP_BACKWARD',",
    "                                           'JUMP_BACKWARD_NO_INTERRUPT', 'JUMP_FORWARD',",
    "                                           'JUMP_ABSOLUTE')]",
    "        _lc_declared = getattr(self._current_loop, 'back_edge_block', None)",
    "        _lc_declared_set = set(getattr(self._current_loop, 'back_edge_blocks', None) or set())",
    "        if _lc_declared is not None:",
    "            _lc_declared_set.add(_lc_declared)",
    "        if (not _lc_payload",
    "                and block not in _lc_declared_set",
    "                and block.start_offset != max(_lc_b.start_offset for _lc_b in _lc_body)):",
    "            return False",
]


def sha16(b):
    return hashlib.sha256(b).hexdigest()[:16]


def main():
    target = sys.argv[1]
    raw = open(target, 'rb').read()
    pre = sha16(raw)
    assert raw.startswith(b'\xef\xbb\xbf'), 'expected BOM'
    assert raw.count(b'\n') == raw.count(b'\r\n'), 'mixed newlines - refuse'
    lines = raw.split(b'\r\n')
    print('target=%s size=%d sha16=%s lines=%d' % (target, len(raw), pre, len(lines)))

    a1 = b"        _lc_body = set(getattr(self._current_loop, 'body_blocks', None) or []) | {_lc_hdr}"
    hit = [n for n, l in enumerate(lines) if l == a1]
    assert len(hit) == 1, 'anchor hit %dx' % len(hit)
    s = hit[0]
    tail = [b"        if not all(p in _lc_body for p in _lc_preds):",
            b"            return False",
            b"        return True"]
    assert lines[s + 1:s + 4] == tail, 'unexpected tail %r' % (lines[s + 1:s + 4],)
    ctx = b'\r\n'.join(lines[max(0, s - 45):s])
    assert b'def _is_loop_tail_convergence_block' in ctx, 'not inside the predicate'

    out = lines[:s + 3] + [x.encode('utf-8') for x in NEW] + lines[s + 3:]
    patched = b'\r\n'.join(out)
    open(target, 'wb').write(patched)
    py_compile.compile(target, doraise=True)
    print('installed %d lines at %d..%d size=%d sha16=%s (was %s) py_compile=OK'
          % (len(NEW), s + 3, s + 2 + len(NEW), len(patched), sha16(patched), pre))


if __name__ == '__main__':
    main()
