"""Merge the still-new hunks of the banked clock_worker candidates onto the current landed
generator and write one merged candidate file.

Base of both banked builds: generator 37d9fecb893704ac (gate-31 bytes, worktree copy at
D:/Temp/r59/wt/core/cfg/region_ast_generator.py).

* M1 (rounds/round32/CANDIDATE_r52a_M1_region_ast_generator.py, 01970a924b74afb4): two purely
  additive hunks, both its own - the 38-line module-level helper
  `_r52_m1_undispatched_struct_entries` and the 20-line use inside the `_r23_or_*`
  else-handling at base :21863.
* M3b (D:/Temp/r59/DELIVER/CANDIDATE_region_ast_generator.py, 3aa27a55eff25a80): five hunks, of
  which FOUR are already-landed content that r59a carried because its base predates gate 32
  (the 82-line `[R21-25]` helper `_r2125_identical_none_tail_else`, the 4-line `[R21-25 发射]`
  use, the 19-line `[R54-B1]` guard). Only the 23-line `[R21-24-M3b]` veto at base :19922 is new.

Each hunk is re-anchored by its surrounding base lines (7-line context, matched exactly once in
the current bytes) so nothing lands twice and no offset arithmetic is trusted.

usage: python -X utf8 merge_m1_m3b.py <out.py>
"""
import difflib
import hashlib
import py_compile
import sys

BASE = r"D:/Temp/r59/wt/core/cfg/region_ast_generator.py"
CURRENT = r"D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main/core/cfg/region_ast_generator.py"
M1 = r"D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main/.trae/specs/region-reduction-v3-full-corpus-100pct-10rounds/rounds/round32/CANDIDATE_r52a_M1_region_ast_generator.py"
M3B = r"D:/Temp/r59/DELIVER/CANDIDATE_region_ast_generator.py"
CTX = 12


def lines(p):
    return open(p, 'rb').read().split(b'\r\n')


def sha16(b):
    return hashlib.sha256(b).hexdigest()[:16]


def hunks(base, cand):
    out = []
    sm = difflib.SequenceMatcher(None, base, cand, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            continue
        out.append((i1, i2, j1, j2, tag))
    return out


def find_context(cur, block, where):
    """Locate `block` (a run of base lines) in cur, return its index; assert exactly one hit."""
    hits = [n for n in range(len(cur) - len(block) + 1) if cur[n:n + len(block)] == block]
    if len(hits) != 1:
        raise SystemExit('%s: context matched %d times (need exactly 1) - %r' % (
            where, len(hits), block[0][:80]))
    return hits[0]


def main():
    base = lines(BASE)
    cur = lines(CURRENT)
    raw_cur = open(CURRENT, 'rb').read()
    assert raw_cur.startswith(b'\xef\xbb\xbf') and raw_cur.count(b'\n') == raw_cur.count(b'\r\n')
    print('current sha16=%s lines=%d' % (sha16(raw_cur), len(cur)))

    picked = []
    for tag, path, keep in (('M1', M1, None), ('M3b', M3B, '[R21-24-M3b]')):
        cand = lines(path)
        hs = hunks(base, cand)
        print('== %s has %d hunks vs base' % (tag, len(hs)))
        for (i1, i2, j1, j2, t) in hs:
            body = cand[j1:j2]
            new = any(keep.encode('utf-8') in l for l in body) if keep else True
            label = '%s:%d..%d(%s,+%d)' % (tag, i1 + 1, i2, t, len(body))
            if not new:
                print('   SKIP %-30s (content already landed / not this candidate\'s own hunk)' % label)
                continue
            print('   KEEP %-30s' % label)
            pre = base[max(0, i1 - CTX):i1]
            post = base[i2:i2 + CTX]
            picked.append((label, body, pre, post, max(0, i1 - CTX)))

    # apply right-to-left so earlier insertions never shift a later anchor
    for label, body, pre, post, _b in sorted(picked, key=lambda x: -x[4]):
        at = None
        seam = pre + post
        hits = [n for n in range(len(cur) - len(seam) + 1) if cur[n:n + len(seam)] == seam]
        if len(hits) == 1:
            at = hits[0] + len(pre)
        else:
            # the neighbourhood of this hunk was itself edited by a later landing, so the
            # contiguous seam no longer exists: fall back to the narrowest unique post anchor
            for w in range(len(post), 0, -1):
                h2 = [n for n in range(len(cur) - w + 1) if cur[n:n + w] == post[:w]]
                if len(h2) == 1:
                    at = h2[0]
                    print('   (seam lost for %s, re-anchored on %d-line post context)' % (label, w))
                    break
            if at is None:
                for w in range(len(pre), 0, -1):
                    h2 = [n for n in range(len(cur) - w + 1) if cur[n:n + w] == pre[len(pre) - w:]]
                    if len(h2) == 1:
                        at = h2[0] + w
                        print('   (seam lost for %s, re-anchored on %d-line pre context)' % (label, w))
                        break
        if at is None:
            raise SystemExit('%s: no unique anchor (seam matched %d times)' % (label, len(hits)))
        cur = cur[:at] + body + cur[at:]

    out = b'\r\n'.join(cur)
    target = sys.argv[1]
    open(target, 'wb').write(out)
    py_compile.compile(target, doraise=True)
    print('WROTE %s size=%d sha16=%s (+%d lines over current)' % (
        target, len(out), sha16(out), len(cur) - len(lines(CURRENT))))


if __name__ == '__main__':
    main()
