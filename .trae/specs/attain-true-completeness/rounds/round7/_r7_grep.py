import io
import re
import sys

path = sys.argv[1]
pattern = sys.argv[2]
ctx = int(sys.argv[3]) if len(sys.argv) > 3 else 0
lines = io.open(path, encoding='utf-8').read().splitlines()
rx = re.compile(pattern)
hits = [i for i, l in enumerate(lines) if rx.search(l)]
print('hits', len(hits))
for i in hits[:60]:
    print('%d: %s' % (i + 1, lines[i].strip()[:160]))
    for j in range(1, ctx + 1):
        if i + j < len(lines):
            print('   %d: %s' % (i + j + 1, lines[i + j].strip()[:160]))
