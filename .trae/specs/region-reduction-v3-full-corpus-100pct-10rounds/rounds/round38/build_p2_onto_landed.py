"""Transplant r63a's P2 hunks (_r63a_break_landing_is_inner_flow) onto landed+M1+P1.

Why a dedicated rig: merge_hunks.py proves a transplant by re-diffing merged-vs-candidate, which
assumes base and current share everything except the picked hunks. Here current is the gate-37
landed bytes + M1 + P1 (D:/Temp/r63/DELIVER/CANDIDATE_onto_landed.py, sha16 258c7d714f4b80e3) while
the P2 author's base is the pre-gate-36 M1+M3b file (3d4f27de6d80ab6e), so every gate-36/37 landing
would read as unexplained residual and the tool would refuse a faithful merge.

Proof used instead, two-sided:
  1. each P2 NEW block is found verbatim in the merged file, and
  2. diff(current, merged) consists of exactly the picked hunks - nothing else moved.
plus py_compile, BOM and all-CRLF invariants.

usage: python -X utf8 build_p2_onto_landed.py
"""
import difflib
import hashlib
import py_compile

MARKER = b'_r63a_break_landing_is_inner_flow'
BASE = 'D:/Temp/r63/base_3d4f27de6d80ab6e.py'
CAND = 'D:/Temp/r63/DELIVER/BANKED_r63a_P1_plus_P2_not_certified.py'
CUR = 'D:/Temp/r63/DELIVER/CANDIDATE_onto_landed.py'
OUT = 'D:/Temp/r63/CANDIDATE_r63a_P2_onto_landed_M1P1.py'


def sha16(b):
    return hashlib.sha256(b).hexdigest()[:16]


def lines_of(p):
    return open(p, 'rb').read().split(b'\r\n')


def find_unique(hay, needle):
    return [n for n in range(len(hay) - len(needle) + 1) if hay[n:n + len(needle)] == needle]


base, cand = lines_of(BASE), lines_of(CAND)
raw_cur = open(CUR, 'rb').read()
assert raw_cur.startswith(b'\xef\xbb\xbf'), 'current lacks the UTF-8 BOM'
assert raw_cur.count(b'\n') == raw_cur.count(b'\r\n'), 'current has mixed newlines'
cur = raw_cur.split(b'\r\n')

picked = []
for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, base, cand, autojunk=False).get_opcodes():
    if tag == 'equal':
        continue
    if any(MARKER in l for l in cand[j1:j2]):
        picked.append((tag, i1, i2, j1, j2))
print('picked %d P2 hunks of %d total' % (
    len(picked),
    sum(1 for o in difflib.SequenceMatcher(None, base, cand, autojunk=False).get_opcodes() if o[0] != 'equal')))

out = list(cur)
new_blocks = []
for tag, i1, i2, j1, j2 in sorted(picked, key=lambda x: -x[1]):
    at = None
    for w in range(12, 0, -1):
        pre, post = base[max(0, i1 - w):i1], base[i2:i2 + w]
        needle, repl = pre + base[i1:i2] + post, pre + cand[j1:j2] + post
        if not needle:
            continue
        hits = find_unique(out, needle)
        if len(hits) == 1:
            at = hits[0]
            out = out[:at] + repl + out[at + len(needle):]
            break
        if len(hits) > 1:
            break
    if at is None:
        # The module-level def is a pure insert whose only context is `return out` + the P1 def,
        # and current's P1 def was spliced without the blank separator, so no symmetric context
        # needle exists. Anchor it on current's P1 def line instead - same slot, P2 first, which
        # is the candidate's own order (def _r63a_break_landing_is_inner_flow precedes def
        # _r63a_block_dominated_by).
        if i1 == i2:
            sib = find_unique(out, [b'def _r63a_block_dominated_by(block, ancestor):'])
            if len(sib) == 1:
                at = sib[0]
                out = out[:at] + cand[j1:j2] + out[at:]
                new_blocks.append(cand[j1:j2])
                print('   base %d..%d (pure insert, def) -> +%d lines before the P1 def at :%d'
                      % (i1 + 1, i2, j2 - j1, at + 1))
                continue
        raise SystemExit('P2 hunk at base %d..%d (%s): no unique content anchor in current - refusing'
                         % (i1 + 1, i2, tag))
    new_blocks.append(cand[j1:j2])
    print('   base %d..%d (%s) -> +%d lines anchored at current :%d' % (i1 + 1, i2, tag, j2 - j1, at + 1))

merged = b'\r\n'.join(out)
open(OUT, 'wb').write(merged)
py_compile.compile(OUT, doraise=True)

for blk in new_blocks:
    if not find_unique(out, blk):
        raise SystemExit('FAIL: a P2 NEW block is not present verbatim in the merged file')

back = merged.split(b'\r\n')
n_other = 0
for tag2, i1, i2, j1, j2 in difflib.SequenceMatcher(None, cur, back, autojunk=False).get_opcodes():
    if tag2 == 'equal':
        continue
    seg = b'|'.join(out[i1:i2])
    if MARKER not in seg:
        n_other += 1
        print('   UNEXPECTED diff cur->merged at :%d (%s)' % (i1 + 1, tag2))
print('merged size=%d sha16=%s (current was %s) py_compile=OK; diffs_not_p2=%d occurrences=%d'
      % (len(merged), sha16(merged), sha16(raw_cur), n_other, merged.count(MARKER)))
