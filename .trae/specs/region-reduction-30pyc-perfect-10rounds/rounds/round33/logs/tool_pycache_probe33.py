# -*- coding: utf-8 -*-
"""Are copied __pycache__ entries a real invalidation risk for the mirror arms?

For every .pyc under a root: read the 4-byte flags field.
  bit 0 set  -> hash-based pyc; bit 1 set -> CHECKED_HASH (source hash verified on every
                import) ; bit 1 clear -> UNCHECKED_HASH (**never** verified: the stale-bytecode trap)
  bit 0 clear -> timestamp pyc: header carries (source_mtime, source_size); it is used only if
                both still match the .py on disk.
Print a verdict per file and a single summary line.

  python -X utf8 pycache_probe33.py <root> [<root> ...]
"""
import io
import os
import struct
import sys

sys.stdout.reconfigure(encoding='utf-8')
DANGEROUS, STALE_OK, FRESH = [], [], 0
STALE, ABSENT = [], []
roots = sys.argv[1:]
assert roots, 'give at least one root'
for root in roots:
    for dp, dn, fn in os.walk(root):
        for f in fn:
            if not f.endswith('.pyc'):
                continue
            p = os.path.join(dp, f)
            b = io.open(p, 'rb').read(16)
            assert len(b) >= 16, p
            flags = struct.unpack('<I', b[4:8])[0]
            src = None
            # PEP 3147: <dir>/__pycache__/<module>.cpython-311.pyc <- <dir>/<module>.py ;
            # legacy layout keeps module.pyc beside module.py.
            mod = f.split('.')[0]
            parent = os.path.dirname(dp)
            for c in (os.path.join(parent, mod + '.py'), os.path.join(dp, mod + '.py'),
                      p[:-4] + '.py'):
                if os.path.isfile(c):
                    src = c
                    break
            if flags & 1:
                (DANGEROUS if not (flags & 2) else STALE_OK).append(
                    '%s flags=%d hash-based %s' % (p, flags, 'checked' if flags & 2 else 'UNCHECKED'))
                continue
            e_mtime, e_size = struct.unpack('<II', b[8:16])
            if src is None:
                ABSENT.append(p)
                STALE_OK.append('%s flags=%d no source beside it (never importable as a mirror)'
                                % (p, flags))
                continue
            st = os.stat(src)
            if int(st.st_mtime) == e_mtime and st.st_size == e_size:
                FRESH += 1
                print('VALID-TIMESTAMP %s  (source mtime+size match)' % p)
            else:
                STALE.append('%s flags=%d recorded %d/%d vs source %d/%d'
                             % (p, flags, e_mtime, e_size, int(st.st_mtime), st.st_size))
                STALE_OK.append('%s flags=%d stale (recorded %d/%d vs %d/%d) -> recompiled'
                                % (p, flags, e_mtime, e_size, int(st.st_mtime), st.st_size))
print('SUMMARY roots=%d pyc_total=%d valid-timestamp(USED)=%d stale-recompiled=%d '
      'no-source-beside=%d unchecked-hash=%d'
      % (len(roots), FRESH + len(STALE) + len(ABSENT) + len(DANGEROUS), FRESH,
         len(STALE), len(ABSENT), len(DANGEROUS)))
for x in STALE[:4]:
    print('  STALE     ' + x)
for x in DANGEROUS:
    print('  DANGEROUS ' + x)
