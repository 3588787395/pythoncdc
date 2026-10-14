"""Compare every swept product against the committed (HEAD) product, CR-stripped, and list the
files whose bytes changed. `git archive HEAD site-packages` output in <headdir> stands for
`git show HEAD:<path>` (HEAD stores LF, checkout converts to CRLF, so a naive cmp flags everything).

usage: python -X utf8 work/sweep_cmp.py <sweepdir> <headdir> <pathlist>
"""
import os
import sys

sweepdir, headdir, listfile = sys.argv[1], sys.argv[2], sys.argv[3]
rels = [l.strip() for l in open(listfile, encoding='utf-8') if l.strip()]


def strip_cr(b):
    return b.replace(b'\r\n', b'\n').replace(b'\r', b'\n')


changed = []
missing = []
same = 0
for rel in rels:
    mine = os.path.normpath(os.path.join(sweepdir, rel[:-4] + '.py'))
    head = os.path.normpath(os.path.join(headdir, rel[:-4] + 'OK.py'))
    if not os.path.isfile(mine):
        missing.append(rel + ' (no swept product)')
        continue
    if not os.path.isfile(head):
        missing.append(rel + ' (no committed product)')
        continue
    a = strip_cr(open(mine, 'rb').read())
    b = strip_cr(open(head, 'rb').read())
    if a == b:
        same += 1
    else:
        changed.append((rel, len(b), len(a)))
print('compared=%d identical=%d CHANGED=%d missing=%d' % (len(rels), same, len(changed), len(missing)))
for rel, hb, mb in changed:
    print('  CHANGED %-62s head=%dB swept=%dB' % (rel, hb, mb))
for m in missing:
    print('  MISSING', m)
