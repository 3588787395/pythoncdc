"""Land R47-A byte-exactly: copy the verified arm generator bytes into the repo.

Refuses unless the arm file is a pure 34-line insertion over the current landed bytes,
keeps BOM/CRLF, and re-verifies every byte property after writing.
"""
import difflib
import hashlib
import io
import sys

REPO = r'F:\Downloads\pythoncdc-main\core\cfg\region_ast_generator.py'
ARM = r'D:\Temp\r43gate\mirr_r47aA\core\cfg\region_ast_generator.py'
sys.stdout.reconfigure(encoding='utf-8')

LAND_SHA = 'b8bfc794dc6c852e7d9c'
LAND_LEN = 3000351
LAND_CRLF = 48620
ARM_SHA = '2a3d522b0ec9e8fe66e4'
ARM_LEN = 3003323
ARM_CRLF = 48654


def props(b):
    return (hashlib.sha256(b).hexdigest()[:20], len(b), b.count(b'\r\n'),
            b.count(b'\n') - b.count(b'\r\n'), b[:3] == b'\xef\xbb\xbf')


old = io.open(REPO, 'rb').read()
new = io.open(ARM, 'rb').read()
assert props(old)[:4] == (LAND_SHA, LAND_LEN, LAND_CRLF, 0) and props(old)[4], 'landed bytes drifted: %r' % (props(old),)
assert props(new)[:4] == (ARM_SHA, ARM_LEN, ARM_CRLF, 0) and props(new)[4], 'arm bytes wrong: %r' % (props(new),)
a = old.decode('utf-8-sig').split('\n')
b = new.decode('utf-8-sig').split('\n')
ops = [o for o in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes() if o[0] != 'equal']
assert len(ops) == 1 and ops[0][0] == 'insert' and ops[0][2] - ops[0][1] == 0 and ops[0][4] - ops[0][3] == 34, ops
io.open(REPO, 'wb').write(new)
after = props(io.open(REPO, 'rb').read())
assert after[:4] == (ARM_SHA, ARM_LEN, ARM_CRLF, 0) and after[4], after
print('LANDED generator', after)
print('insert at landed line', ops[0][1] + 1, '->', 34, 'lines')
