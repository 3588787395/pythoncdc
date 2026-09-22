# -*- coding: utf-8 -*-
"""Round 30 G6/G7 archiving: write logs/stats30.txt verbatim and logs/index_delta30.txt as a
per-field diff of pyc_index.json (git HEAD, i.e. pre-round-30, vs the working file the
batch just wrote back).  Nothing is typed from memory.

  python -X utf8 ixdelta30.py [--apply]
"""
import io
import json
import os
import subprocess
import sys

REPO = r'F:\Downloads\pythoncdc-main'
LOGS = os.path.join(REPO, r'.trae\specs\region-reduction-30pyc-perfect-10rounds\rounds\round30\logs')
RAW = r'D:/Temp/r30gate/c1/stats30_raw.txt'
BS = os.sep


def load(blob):
    d = json.loads(blob.decode('utf-8'))
    assert isinstance(d, list)
    return d


PREFIX = 'site-packages/'


def short(path):
    i = path.find(PREFIX)
    return path[i + len(PREFIX):].replace('\\', '/') if i >= 0 else path


def main():
    stats = io.open(RAW, encoding='utf-8').read()
    assert 'cumulative_match_rate' in stats and stats.count('===') >= 2, 'stats output malformed'
    old_blob = subprocess.check_output(['git', 'show', 'HEAD:pyc_index.json'], cwd=REPO)
    new_raw = io.open(os.path.join(REPO, 'pyc_index.json'), 'rb').read()
    old = load(old_blob)
    new = load(new_raw)
    assert len(old) == 402 and len(new) == 402, (len(old), len(new))
    assert [e['path'] for e in old] == [e['path'] for e in new], 'index entry list/order changed'

    fields = sorted({k for e in old for k in e} | {k for e in new for k in e})
    out = []
    touched = []
    real = set()
    for f in fields:
        rows = []
        for a_e, b_e in zip(old, new):
            a, b = a_e.get(f), b_e.get(f)
            if a != b:
                rows.append((short(a_e['path']), a, b))
        if not rows:
            continue
        touched.append(f)
        if f != 'last_tested_round':
            real.update(k for k, _, _ in rows)
        out.append('%-28s changed in %d entries' % (f, len(rows)))
        for key, a, b in rows:
            if f == 'last_tested_round' and len(rows) > 20:
                continue  # the round stamp moves for every entry; not evidence
            out.append('    %-72s %s -> %s' % (key, a, b))
        if f == 'last_tested_round' and len(rows) > 20:
            out.append('    (... all %d entries re-stamped %s -> %s, list elided)'
                       % (len(rows), old[0].get('last_tested_round'), new[0].get('last_tested_round')))
    out.append('total fields touched: %s' % touched)
    out.append('entries compared: %d, path list identical: True' % len(old))
    out.append('entries with real (non round-stamp) field changes: %d -> %s'
               % (len(real), sorted(real)))
    text = u'\r\n'.join(out) + u'\r\n'

    dst1 = os.path.join(LOGS, 'stats30.txt')
    dst2 = os.path.join(LOGS, 'index_delta30.txt')
    print('stats -> %s (%d chars)' % (dst1, len(stats)))
    print(text)
    if '--apply' not in sys.argv:
        print('dry run')
        return
    io.open(dst1, 'wb').write(stats.replace(u'\r\n', u'\r\n').encode('utf-8'))
    io.open(dst2, 'wb').write(text.encode('utf-8'))
    a = io.open(dst1, 'rb').read()
    b = io.open(dst2, 'rb').read()
    assert b.count(b'\n') == b.count(b'\r\n'), 'index_delta is not pure CRLF'
    assert a.decode('utf-8').count('cumulative_match_rate') == 1
    print('wrote %s %dB  %s %dB' % (os.path.basename(dst1), len(a), os.path.basename(dst2), len(b)))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
