"""Coverage audit v2 — separate real decompiler inputs from derived caches.

The objective is per-pyc: every .pyc in site-packages must decompile and have a same-directory
`<name>OK.py`. A walk that counts every .pyc counts `__pycache__/<mod>OK.cpython-311.pyc`, which is
the cache Python wrote when it IMPORTED our own product - a derived artifact, not an input. This
script classifies every .pyc and reports the two numbers that actually matter: inputs lacking a
product, and products whose name does not match an input.

usage: python -X utf8 coverage_audit2.py
"""
import collections
import os

SEP = chr(92)
root = os.path.abspath('site-packages')
MAGIC311 = b'\xa7\r\r\n'
all_pyc = []
for dirpath, dirnames, filenames in os.walk(root, onerror=lambda e: None):
    for f in filenames:
        if f.endswith('.pyc'):
            all_pyc.append(os.path.join(dirpath, f))
oks = set()
for dirpath, dirnames, filenames in os.walk(root, onerror=lambda e: None):
    for f in filenames:
        if f.endswith('OK.py'):
            oks.add(os.path.join(dirpath, f))

derived, inputs = [], []
for p in all_pyc:
    rel = os.path.relpath(p, root).replace(SEP, '/')
    head = open(p, 'rb').read(4)
    is_cache_dir = (os.sep + '__pycache__' + os.sep) in p
    if is_cache_dir:
        derived.append(p)
    else:
        inputs.append((p, head))

print('total .pyc            = %d' % len(all_pyc))
print('derived (__pycache__) = %d  (Python caches of our own *OK.py, not inputs)' % len(derived))
print('real inputs           = %d' % len(inputs))
missing = [p for p, h in inputs if os.path.dirname(p) + os.sep + os.path.basename(p)[:-4] + 'OK.py' not in oks]
print('INPUTS missing <name>OK.py : %d' % len(missing))
for p in missing[:20]:
    print('   ', os.path.relpath(p, root).replace(SEP, '/'))
odd_magic = [(p, h) for p, h in inputs if h != MAGIC311]
print('inputs whose magic is not 3.11 : %d' % len(odd_magic))
for p, h in odd_magic[:12]:
    print('    %s  magic=%s  size=%d' % (os.path.relpath(p, root).replace(SEP, '/'),
                                         h.hex(), os.path.getsize(p)))
bad_names = sorted(p for p in oks if ' ' in os.path.basename(p))
print('products with a SPACE in the name (naming slip): %d' % len(bad_names))
for p in bad_names:
    want = os.path.dirname(p) + os.sep + os.path.basename(p).replace(' OK.py', 'OK.py')
    print('    %s   proper twin exists=%s' % (os.path.relpath(p, root).replace(SEP, '/'),
                                              os.path.exists(want)))
dup = collections.Counter(os.path.basename(p) for p in oks)
print('product basenames reused in >1 dir: %d (expected: duplicated modules across packages)'
      % sum(1 for v in dup.values() if v > 1))
