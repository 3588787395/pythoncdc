"""R21-40a: give the trailing continue to the ARM that owns it instead of to the Try body tail.

Measured progression on trade_live_broker._process_cancel_order (allwin window printer, same judge):
  landed bytes                      delta=-1 hunks=3   (spurious JUMP_BACKWARD after COPY/POP_EXCEPT/
                                                   RERAISE + both arm continues missing)
  + [R21-35a] generator half        delta=-2 hunks=2   (handler jump and outer-else jump fixed; the
                                                   inner else arm's continue is at the body tail, so the
                                                   body's normal-completion edge @1826 never appears)
  + [R21-40] analyzer half only     delta= 0 hunks=2   (outer-else continue correct; the inner else
                                                   arm's continue is now missing)
  + BOTH halves (the pair)          delta=-1 hunks=1   (only @1826 JUMP_FORWARD missing)
The one surviving instruction is the `try` body's normal-completion edge: in the original the
`elif ... node_type == '7': pass` arm and the `error_no == 0` arm jump PAST the whole try statement
(@1826 JUMP_FORWARD -> @2000, the `time.sleep`), while the inner `else` arm alone ends with
`continue` (@1824 JUMP_BACKWARD -> @44, the loop's continue re-entry NOP). [R21-35a] appends its
Continue to `body_stmts`, i.e. to the body tail, which forces EVERY normal-completion path of that
body onto the continue and deletes the body-end edge.

Fix: keep the same claim (the same five-condition screen, the same `generated_blocks` bookkeeping),
but hand the Continue to the arm the back-edge block's predecessor belongs to. Identity is read from
region-declared data only: `_r35_src` (the predecessor block of the pure back-edge block, already
known at that point in the landed code) must be a member of an IfRegion's `else_blocks`, and the
statement the body ends with must be that If with an existing `orelse` list. Otherwise the behavior
is byte-identical to [R21-35a] (the previous append), so the hunk is a strict refinement, not a
new firing condition. No names, no offsets, no counters, no thresholds.

usage: python -X utf8 build_cand_r38_R21-40a_arm_continue.py <generator-file>
       (the file must already carry the [R21-35a] hunk, i.e. hash a8155727b47e3bea)
"""
import hashlib
import py_compile
import sys

OLD = [
    "                    body_stmts.append({'type': 'Continue'})",
    "                    self.generated_blocks.add(_r35_b)",
]

NEW = [
    "                    _r40a_reg = self.region_analyzer.get_region_for_block(_r35_src)",
    "                    _r40a_arm = None",
    "                    if (_r40a_reg is not None and isinstance(_r40a_reg, IfRegion)",
    "                            and _r35_src in (getattr(_r40a_reg, 'else_blocks', None) or [])",
    "                            and body_stmts and isinstance(body_stmts[-1], dict)",
    "                            and body_stmts[-1].get('type') == 'If'",
    "                            and isinstance(body_stmts[-1].get('orelse'), list)):",
    "                        _r40a_arm = body_stmts[-1]['orelse']",
    "                    if _r40a_arm is not None:",
    "                        # [R21-40a] 回边块的前驱属于某个 IfRegion 的 else 臂 ⇒ Continue 归该臂，",
    "                        # try 体的正常完成路径因此保留自己的块尾跳转（实测 @1826 JUMP_FORWARD）。",
    "                        _r40a_arm.append({'type': 'Continue'})",
    "                    else:",
    "                        body_stmts.append({'type': 'Continue'})",
    "                    self.generated_blocks.add(_r35_b)",
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
    ob = [x.encode('utf-8') for x in OLD]
    hits = [n for n in range(len(lines) - len(ob) + 1) if lines[n:n + len(ob)] == ob]
    assert len(hits) == 1, 'anchor hits %d (the [R21-35a] claim must be unique)' % len(hits)
    n = hits[0]
    ctx = b'\r\n'.join(lines[max(0, n - 30):n])
    assert b'_r35_pay' in ctx, 'anchor is not inside the [R21-35] continue claim'
    out = lines[:n] + [x.encode('utf-8') for x in NEW] + lines[n + len(OLD):]
    patched = b'\r\n'.join(out)
    open(target, 'wb').write(patched)
    py_compile.compile(target, doraise=True)
    print('replaced %d with %d lines at :%d size=%d sha16=%s (was %s) py_compile=OK'
          % (len(OLD), len(NEW), n + 1, len(patched), sha16(patched), pre))


if __name__ == '__main__':
    main()
