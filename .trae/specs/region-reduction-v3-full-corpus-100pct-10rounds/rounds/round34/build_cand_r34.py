"""R34 candidate builder: the terminal-block conjunct on the P1-3b Continue suppression.

usage: python -X utf8 build_cand_r34.py <generator-file-to-patch> [--revert <backup>]

Patches `RegionASTGenerator._is_loop_tail_convergence_block` so a back-edge block is
only treated as a "natural loop-tail convergence" (=> explicit Continue suppressed)
when it is the loop body's TERMINAL block. An interior back-edge block skips later
loop-body statements, so it is a source-level `continue` and must be emitted
(trade_live_broker.ipo_stocks_order block @3572: delta=-1, one JUMP_BACKWARD missing).

Byte-level and BOM/CRLF preserving: the file is BOM + all-CRLF with 0 bare LF, so
splitting on b'\r\n' and rejoining is lossless. Every anchor is asserted, so a base
drift fails loudly instead of silently patching the wrong line.
"""
import hashlib
import py_compile
import shutil
import sys

NEW = [
    "        # [R21-28] 收尾块才可抑制：for/while 重编译只自然再生循环体收尾的那条回边；本体内",
    "        # 仍有更高偏移块时，本块回边跳过了它们（ipo_stocks_order @3572 跳过 @3576 跳板与",
    "        # @3640 起的下单语句），是源码显式 continue，抑制会少发一条 JUMP_BACKWARD。",
    "        if block.start_offset != max(_lc_b.start_offset for _lc_b in _lc_body):",
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
    a2 = b"        if not all(p in _lc_body for p in _lc_preds):"
    a3 = b"            return False"
    a4 = b"        return True"
    i1 = [n for n, l in enumerate(lines) if l == a1]
    assert len(i1) == 1, 'anchor _lc_body assignment hit %dx' % len(i1)
    s = i1[0]
    assert lines[s + 1] == a2 and lines[s + 2] == a3 and lines[s + 3] == a4, (
        'expected the 4-line tail of _is_loop_tail_convergence_block, got %r'
        % [lines[s + 1], lines[s + 2], lines[s + 3]])
    _ctx = b'\r\n'.join(lines[max(0, s - 45):s])
    assert b'def _is_loop_tail_convergence_block' in _ctx, (
        'anchors matched but not inside _is_loop_tail_convergence_block')

    out = lines[:s + 3] + [x.encode('utf-8') for x in NEW] + lines[s + 3:]
    patched = b'\r\n'.join(out)
    open(target, 'wb').write(patched)
    py_compile.compile(target, doraise=True)
    print('installed lines=%d..%d size=%d sha16=%s (was %s)  py_compile=OK'
          % (s + 3, s + 2 + len(NEW), len(patched), sha16(patched), pre))


if __name__ == '__main__':
    main()
