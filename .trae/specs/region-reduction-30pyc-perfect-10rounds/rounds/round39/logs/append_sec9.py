# -*- coding: utf-8 -*-
"""Byte-level append of DIAGNOSIS.md section 9 (LF-only file; Edit tool forbidden here).

Asserts the current prefix identity, appends the LF-normalised text read from
D:/Temp/r39diagA/sec9_diag.md, then re-asserts the original bytes are an exact prefix.

usage: python -X utf8 append_sec9.py [--apply]
"""
import hashlib
import io
import sys

P = r'F:\Downloads\pythoncdc-main\.trae\specs\region-reduction-30pyc-perfect-10rounds\rounds\round39\DIAGNOSIS.md'
SRC = r'D:\Temp\r39diagA\sec9_diag.md'
EXPECT_SHA20 = '6e0fb1a6e05a7103e648'
EXPECT_LEN = 10612
EXPECT_CRLF = 0
EXPECT_LF = 157

b = io.open(P, 'rb').read()
assert hashlib.sha256(b).hexdigest()[:20] == EXPECT_SHA20, 'stale read: sha mismatch'
assert len(b) == EXPECT_LEN, 'stale read: length mismatch'
assert b.count(b'\r\n') == EXPECT_CRLF and b.count(b'\n') == EXPECT_LF, 'line-ending drift'
add = io.open(SRC, 'rb').read().replace(b'\r\n', b'\n')
assert add.startswith(b'\n## ') and add.endswith(b'\n'), 'section text malformed'
out = b + add
assert out.startswith(b), 'prefix not preserved'
print('append %d bytes -> %d, LF %d -> %d' % (len(add), len(out), b.count(b'\n'), out.count(b'\n')))
if '--apply' not in sys.argv:
    print('dry run; pass --apply')
    sys.exit(0)
io.open(P, 'wb').write(out)
after = io.open(P, 'rb').read()
assert after == out and after.count(b'\r') == 0, 'append not byte-exact'
print('applied: sha20 %s len %d CRLF %d LF %d' % (hashlib.sha256(after).hexdigest()[:20],
                                                  len(after), after.count(b'\r\n'), after.count(b'\n')))
