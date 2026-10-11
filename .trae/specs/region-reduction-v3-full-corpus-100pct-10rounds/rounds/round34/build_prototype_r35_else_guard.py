"""R35 prototype: refuse loop else_blocks that jump back to their own loop header.

Mechanism: a `while/for ... else:` clause runs only AFTER the loop exits, so a block declared in
LoopRegion.else_blocks whose terminator is JUMP_BACKWARD to that same loop's header cannot be
else-clause content - it is a body-tail block the body falls into. Measured population on the
verification face (D:/Temp/r34/else_census.py): 1169 loops have non-empty else_blocks and exactly
3 contain such a block, all in trade_live_broker residual units:
_process_order @3128 (hdr=46), _process_cancel_order @2000 (hdr=46), _trade_status_handle @830 (hdr=46).

usage: python -X utf8 build_prototype_r35_else_guard.py <analyzer-file>
"""
import hashlib
import py_compile
import sys

NEW = [
    "            # [R21-33 原型] while/for-else 子句在循环退出后才执行，其块的回边不可能指向本循环",
    "            # header；若 else_blocks 中某块末指令是 JUMP_BACKWARD 且目标 offset 恰为 header 起点，",
    "            # 该块其实是体内收尾块（被某条臂顺序/跳转落入），归 body 才与原字节码同形。",
    "            # 语料实测：1169 个非空 else_blocks 循环中恰 3 个含此类块，全在 trade_live_broker",
    "            # 残余单元 (_process_order @3128 / _process_cancel_order @2000 / _trade_status_handle @830)。",
    "            if else_blocks and header is not None:",
    "                _r33_keep = []",
    "                _r33_move = []",
    "                for _r33_b in else_blocks:",
    "                    _r33_last = None",
    "                    for _r33_i in reversed(_r33_b.instructions):",
    "                        if _r33_i.opname in ('NOP', 'CACHE', 'EXTENDED_ARG'):",
    "                            continue",
    "                        _r33_last = _r33_i",
    "                        break",
    "                    if (_r33_last is not None",
    "                            and _r33_last.opname in ('JUMP_BACKWARD',",
    "                                                     'JUMP_BACKWARD_NO_INTERRUPT')",
    "                            and _r33_last.argval == header.start_offset):",
    "                        _r33_move.append(_r33_b)",
    "                    else:",
    "                        _r33_keep.append(_r33_b)",
    "                if _r33_move:",
    "                    else_blocks = _r33_keep",
    "                    ordered_body = list(ordered_body) + _r33_move",
    "            region.else_blocks = else_blocks",
]


def sha16(b):
    return hashlib.sha256(b).hexdigest()[:16]


def main():
    target = sys.argv[1]
    raw = open(target, 'rb').read()
    pre = sha16(raw)
    crlf, lf_only = raw.count(b'\r\n'), raw.count(b'\n') - raw.count(b'\r\n')
    NL = b'\r\n' if crlf >= len(raw.split(b'\n')) // 2 else b'\n'
    print('target=%s size=%d sha16=%s CRLF=%d bareLF=%d split_on=%r'
          % (target, len(raw), pre, crlf, lf_only, NL))
    lines = raw.split(NL)
    anchor = b"            region.else_blocks = else_blocks"
    hit = [n for n, l in enumerate(lines) if l == anchor]
    assert len(hit) == 1, 'anchor hit %dx at %s' % (len(hit), hit)
    n = hit[0]
    out = lines[:n] + [x.encode('utf-8') for x in NEW] + lines[n + 1:]
    patched = NL.join(out)
    open(target, 'wb').write(patched)
    py_compile.compile(target, doraise=True)
    print('inserted %d lines at %d (replacing 1) size=%d sha16=%s (was %s) py_compile=OK'
          % (len(NEW), n, len(patched), sha16(patched), pre))


if __name__ == '__main__':
    main()
