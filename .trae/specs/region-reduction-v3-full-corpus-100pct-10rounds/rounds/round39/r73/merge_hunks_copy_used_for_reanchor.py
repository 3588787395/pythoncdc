"""Merge hunks from a candidate file onto a moved base, by content-anchored splices, with proof.

Why this exists: candidates get banked while the base keeps landing new criteria, so installing a
banked WHOLE file silently reverts everything landed after its base. Two incidents forced this tool:
M3b carried four hunks that had already landed under gate 32, and r46a's analyzer half had to be
transplanted around the landed `[R21-33b]` hunk. Both were ad-hoc scripts; this is the general one.

Method: diff base -> candidate. Each non-equal hunk is transplanted by splicing a SPAN - the needle
is the base's context plus the hunk's OLD lines, the replacement is the same context plus the
candidate's NEW lines, so insert and replace are handled by one code path. (An early version only
inserted, which turned every replace hunk into an IndentationError; the known-answer self-test below
caught it.) Hunks are applied right-to-left and anchored by content, never by copied offsets.

Proof requirement, which is the point of the tool: after writing, the merged file is re-diffed
against the candidate and EVERY remaining difference must be explained by the skip marker, or the
tool fails. Self-test with an answer known independently:

  python -X utf8 merge_hunks.py \\
    --base    D:/Temp/r34/pristine_35e227ac3e7b25af_region_analyzer.py \\
    --candidate <repo>/.trae/specs/.../rounds/round31/CANDIDATE_r46a_region_analyzer_BANKED_NOT_LANDED.py \\
    --current D:/Temp/r37/pristine_landed_analyzer_efd455859b69d8a1.py \\
    --expect-residual '[R21-33b]' --out D:/Temp/r37/selftest_merged_analyzer.py
  # merged file MUST hash to c069d359cbfe76b0, the merged analyzer that gate 37 actually landed

usage: python -X utf8 merge_hunks.py --base B --candidate C --current N --out OUT
                                     [--only MARKER] [--skip MARKER] [--expect-residual MARKER]
"""
import argparse
import difflib
import hashlib
import py_compile
import sys


def sha16(path_or_bytes):
    data = open(path_or_bytes, 'rb').read() if isinstance(path_or_bytes, str) else path_or_bytes
    return hashlib.sha256(data).hexdigest()[:16]


def lines_of(path):
    return open(path, 'rb').read().split(b'\r\n')


def find_unique(hay, needle):
    return [n for n in range(len(hay) - len(needle) + 1) if hay[n:n + len(needle)] == needle]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', required=True)
    ap.add_argument('--candidate', required=True)
    ap.add_argument('--current', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--only', default=None, help='keep only hunks whose NEW lines contain this marker')
    ap.add_argument('--skip', default=None, help='drop hunks whose new or replaced lines contain this marker')
    ap.add_argument('--expect-residual', default=None)
    ap.add_argument('--ctx', type=int, default=12)
    a = ap.parse_args()

    base, cand, cur = lines_of(a.base), lines_of(a.candidate), lines_of(a.current)
    raw_cur = open(a.current, 'rb').read()
    assert raw_cur.startswith(b'\xef\xbb\xbf'), 'current lacks the UTF-8 BOM - wrong file?'
    assert raw_cur.count(b'\n') == raw_cur.count(b'\r\n'), 'current has mixed newlines - refuse'

    picked, dropped = [], []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, base, cand, autojunk=False).get_opcodes():
        if tag == 'equal':
            continue
        new, old = cand[j1:j2], base[i1:i2]
        if a.only and not any(a.only.encode() in l for l in new):
            dropped.append(('only', i1 + 1, i2, len(new)))
            continue
        if a.skip and (any(a.skip.encode() in l for l in new) or any(a.skip.encode() in l for l in old)):
            dropped.append(('skip', i1 + 1, i2, len(new)))
            continue
        picked.append((i1, i2, j1, j2))

    out = list(cur)
    applied = []
    for i1, i2, j1, j2 in sorted(picked, key=lambda x: -x[0]):
        at = how = None
        for w in range(a.ctx, 0, -1):
            pre, post = base[max(0, i1 - w):i1], base[i2:i2 + w]
            needle, repl = pre + base[i1:i2] + post, pre + cand[j1:j2] + post
            if not needle:
                continue
            hits = find_unique(out, needle)
            if len(hits) == 1:
                at = hits[0]
                how = 'ctx(%d)+%dold' % (w, len(base[i1:i2]))
                out = out[:at] + repl + out[at + len(needle):]
                break
            if len(hits) > 1:
                break
        if at is None:
            raise SystemExit('hunk at base %d..%d: no unique content anchor in current '
                             '(needle ambiguous or absent) - refusing to guess' % (i1 + 1, i2))
        applied.append((i1 + 1, i2, j2 - j1, how))

    merged = b'\r\n'.join(out)
    open(a.out, 'wb').write(merged)
    py_compile.compile(a.out, doraise=True)
    print('applied %d hunks, dropped %d; merged size=%d sha16=%s (current was %s)'
          % (len(applied), len(dropped), len(merged), sha16(merged), sha16(raw_cur)))
    for i1, i2, n, how in applied:
        print('   base %d..%d -> +%d lines via %s' % (i1 + 1, i2, n, how))
    for d in dropped:
        print('   dropped %s base %d..%d (+%d)' % d)

    back = merged.split(b'\r\n')
    resid = [o for o in difflib.SequenceMatcher(None, back, cand, autojunk=False).get_opcodes()
             if o[0] != 'equal']
    unexplained = 0
    print('residual merged-vs-candidate: %d blocks' % len(resid))
    for tag2, i1, i2, j1, j2 in resid:
        has = bool(a.expect_residual) and any(a.expect_residual.encode() in l for l in back[i1:i2])
        print('   %-7s merged %d..%d (%d) vs cand %d..%d (%d) explained-by-marker=%s'
              % (tag2, i1 + 1, i2, i2 - i1, j1 + 1, j2, j2 - j1, has))
        if not has:
            unexplained += 1
    if unexplained:
        raise SystemExit('FAIL: %d residual block(s) not explained by --expect-residual: the merge '
                         'did not transplant the candidate faithfully' % unexplained)
    print('OK: every residual block is explained; merge is faithful')


if __name__ == '__main__':
    main()
