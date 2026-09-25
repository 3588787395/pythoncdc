# -*- coding: utf-8 -*-
"""Round 67 centre 402-file corpus sweep driver (background-friendly, resumable).

  python -X utf8 sweep402_67.py <arm> [<arm2> ...]

Runs every arm over `all402.txt` in 4 shards so no single child exceeds the 300 s rule;
`h62.py run` appends and skips records already present in the out file, so an interrupted
sweep resumes. Prints a per-shard tail and a final record count.
"""
import io
import os
import subprocess
import sys

GATE = r'D:/Temp/opencode/r67gate/center'
sys.stdout.reconfigure(encoding='utf-8')

def count(out):
    return sum(1 for l in io.open(out, encoding='utf-8') if l.strip()) if os.path.isfile(out) else 0


for arm in sys.argv[1:]:
    out = '%s/dump/%s_402.jsonl' % (GATE, arm)
    want = sum(1 for l in io.open(GATE + '/all402.txt', encoding='utf-8') if l.strip())
    for rnd in range(8):
        if count(out) >= want:
            break
        for sh in range(4):
            cmd = [sys.executable, '-X', 'utf8', GATE + '/h62.py', 'run', '--arm=' + arm,
                   '--list=' + GATE + '/all402.txt', '--out=' + out,
                   '--nshard=4', '--shard=%d' % sh, '--budget=270']
            try:
                r = subprocess.run(cmd, cwd=GATE, capture_output=True, text=True, timeout=290,
                                   errors='replace')
                rc, tail = r.returncode, (r.stdout or '').strip().split('\n')[-1:]
            except subprocess.TimeoutExpired as e:
                rc, tail = -9, [(e.stdout or b'' ).decode('utf-8', 'replace').strip().split('\n')[-1:][0]
                                if e.stdout else '']
            print('round %d %s shard %d exit=%s records=%d/%d  last: %s'
                  % (rnd, arm, sh, rc, count(out), want, (tail[0] if tail else '')[:110]), flush=True)
    print('ARM %s done records=%d/%d' % (arm, count(out), want), flush=True)
print('SWEEP DONE %s' % ' '.join(sys.argv[1:]), flush=True)
