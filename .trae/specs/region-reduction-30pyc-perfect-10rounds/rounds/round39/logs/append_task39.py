# -*- coding: utf-8 -*-
"""Byte-level append of Task 39 to tasks.md (Edit tool is forbidden for this file).

Asserts the exact current prefix identity (sha256/len/CRLF/LF counts) before writing, so a
stale read cannot double-append or truncate the user's ledger; appends the CRLF-normalised
text read from D:/Temp/r39diagA/task39.md and re-asserts the original bytes are an exact prefix.

usage: python -X utf8 append_task39.py            # dry run
       python -X utf8 append_task39.py --apply
"""
import hashlib
import io
import sys

T = r'F:\Downloads\pythoncdc-main\.trae\specs\region-reduction-30pyc-perfect-10rounds\tasks.md'
SRC = r'D:\Temp\r39diagA\task39.md'
EXPECT_SHA20 = 'd431bbf33034feeb4e23'
EXPECT_LEN = 189516
EXPECT_CRLF = 1766
EXPECT_LF = 1766

b = io.open(T, 'rb').read()
assert hashlib.sha256(b).hexdigest()[:20] == EXPECT_SHA20, 'stale read: sha mismatch'
assert len(b) == EXPECT_LEN, 'stale read: length mismatch'
assert b.count(b'\r\n') == EXPECT_CRLF and b.count(b'\n') == EXPECT_LF, 'line-ending drift'
assert b.endswith(b'\r\n'), 'ledger does not end on a complete line'

add = io.open(SRC, 'rb').read().replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
assert add.startswith(b'- [x] Task 39:') and add.endswith(b'\r\n'), 'body malformed'
out = b + add
assert out.startswith(b), 'prefix not preserved'
print('append %d bytes -> %d  CRLF %d -> %d' % (len(add), len(out), b.count(b'\r\n'), out.count(b'\r\n')))
if '--apply' not in sys.argv:
    print('dry run; pass --apply')
    sys.exit(0)
io.open(T, 'wb').write(out)
after = io.open(T, 'rb').read()
assert after == out, 'append not byte-exact'
print('applied: sha20 %s len %d CRLF %d LF %d' % (hashlib.sha256(after).hexdigest()[:20], len(after),
                                                  after.count(b'\r\n'), after.count(b'\n')))
