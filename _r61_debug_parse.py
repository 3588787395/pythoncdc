#!/usr/bin/env python3
with open('_r60_full_verify.txt','r',errors='replace') as f:
    r60 = f.readlines()
with open('_r61_full_verify.txt','r',errors='replace') as f:
    r61 = f.readlines()
print(f'R60 lines: {len(r60)}, R61 lines: {len(r61)}')
print('R60 first 5:')
for l in r60[:5]: print(repr(l))
print('R61 first 5:')
for l in r61[:5]: print(repr(l))

# Also try simple line-by-line diff
import difflib
diff = list(difflib.unified_diff(r60, r61, 'R60', 'R61', n=0))
print(f'\nDiff lines: {len(diff)}')
for line in diff[:50]:
    print(line.rstrip())
