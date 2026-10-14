"""Merge the banked r46a quote analyzer half (R21-16 variant D, 8efe7f0040241138) onto the CURRENT
landed analyzer (efd455859b69d8a1 = gate-32 bytes + the R21-33b while-True hunk landed at gate 36).

The candidate's base predates gate 36, so a whole-file install would silently REVERT the landed
while-True criterion. Its hunks live at :11310/:11348/:11376/:12234 and R21-33b lives at
:5948..5964 - disjoint - so the merge is done by diff opcodes applied right-to-left, skipping the
one block that is exactly R21-33b, and then PROVED by re-diffing the merged file against the
candidate: the only remaining difference must be the R21-33b hunk and nothing else.

usage: python -X utf8 merge_r46a_onto_landed.py <out.py>
"""
import difflib
import hashlib
import py_compile
import sys

CUR = r"D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main/core/cfg/region_analyzer.py"
CAND = (r"D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main/.trae/specs/"
        r"region-reduction-v3-full-corpus-100pct-10rounds/rounds/round31/"
        r"CANDIDATE_r46a_region_analyzer_BANKED_NOT_LANDED.py")


def lines(p):
    return open(p, 'rb').read().split(b'\r\n')


def sha16(b):
    return hashlib.sha256(b).hexdigest()[:16]


def main():
    cur, cand = lines(CUR), lines(CAND)
    raw = open(CUR, 'rb').read()
    assert raw.startswith(b'\xef\xbb\xbf') and raw.count(b'\n') == raw.count(b'\r\n'), 'cur bytes'
    out = list(cur)
    applied, skipped = [], []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, cur, cand, autojunk=False).get_opcodes():
        if tag == 'equal':
            continue
        block = cand[j1:j2]
        if any(b'[R21-33b]' in l for l in block) or any(b'[R21-33b]' in l for l in cur[i1:i2]):
            skipped.append((tag, i1 + 1, i2, j1 + 1, j2))
            continue
        applied.append((tag, i1, i2, j1, j2))
    for tag, i1, i2, j1, j2 in sorted(applied, key=lambda x: -x[1]):
        out = out[:i1] + cand[j1:j2] + out[i2:]
    merged = b'\r\n'.join(out)
    target = sys.argv[1]
    open(target, 'wb').write(merged)
    py_compile.compile(target, doraise=True)

    back = lines(target)
    resid = [o for o in difflib.SequenceMatcher(None, back, cand, autojunk=False).get_opcodes()
             if o[0] != 'equal']
    print('applied %d hunks, skipped %d (R21-33b)' % (len(applied), len(skipped)))
    print('merged size=%d sha16=%s (cur was %s)' % (len(merged), sha16(merged), sha16(raw)))
    print('residual diff merged-vs-candidate: %d blocks' % len(resid))
    for tag, i1, i2, j1, j2 in resid:
        print('   %-7s merged %d..%d (%d) vs cand %d..%d (%d) | merged-side marker=%s' % (
            tag, i1 + 1, i2, i2 - i1, j1 + 1, j2, j2 - j1,
            any(b'[R21-33b]' in l for l in back[i1:i2])))


if __name__ == '__main__':
    main()
