# -*- coding: utf-8 -*-
"""Round 31: promote the diagnosing agent's G0 repro pair into the repo's test_repros tree.

Only the leading docstring is rewritten (it claimed every CONTROL stays fully matched on the
landed core, which the measurement contradicts); the executable bodies are copied byte-for-byte
from the agent's files, so the .pyc regenerated here is the same code object the gates measured.

  python -X utf8 prep31repro.py            # dry: print what would be written
  python -X utf8 prep31repro.py --apply    # write pure-CRLF .py + sibling .pyc
"""
import io
import os
import py_compile
import sys

SRC = r'D:/Temp/r31diagA/witness'
DST = r'F:\Downloads\pythoncdc-main\test_repros\round31_arm_terminal_join'
NAMES = ['r31a_witness.py', 'r31a_control.py']

HEADERS = {
    'r31a_witness.py': u'''# -*- coding: utf-8 -*-
"""Round 31 G0 witness (line A, R31-B/R31-C): a nested-if arm whose join block is itself a
terminal hard-exit statement block (bare `raise`, no normal successor), reached inside an
`except ... as e` handler arm.

Same structural reason as `site-packages/fly/common/flytools.pyc ::
<module>.FileLock.acquire` (official ruler 88/85, jump_diffs=2, true_diffs=14).

Measured readings, both cores run through the mirror harness in `D:/Temp/r31gate/c1`:
  landed core (7ee4151d31faf41b8202)   -> 1/4  w_a 52/47 j4 t11 | w_b 48/44 j3 t14
                                                 | w_c 64/63 j2 t51
  R31-C (site 1 + elif-chain replay)    -> 3/4  w_a and w_b matched; w_c unchanged
  R31-B (site 1 only)                   -> 2/4  only w_b matched
So w_a/w_b are the predicate's own witnesses (they FAIL on the landed core and the site-2
replay is what brings w_a back), while w_c is a distinct residual shape that this predicate
deliberately does not reach.
"""
''',
    'r31a_control.py': u'''# -*- coding: utf-8 -*-
"""Round 31 G0 CONTROL battery: near-miss shapes around the R31-B/R31-C arm-stop release.

c1  nested one-arm if whose join block is an ordinary continuation (not terminal)
c2  arm tail is a `break` (last instruction is a forward jump, not an exit op)
c3  bare raise as the whole handler tail, no nested if join before it
c4  raise INSIDE the nested if body (the nested if's join is not the raise)
c5  nested-if terminal join inside a plain (non-handler) loop body arm
c6  nested-if terminal join where BOTH arms of the outer if end in the raise

Measured readings (mirror harness, `D:/Temp/r31gate/c1`): this file reads 5/7 on the landed
core AND 5/7 under R31-B and R31-C, with the two failures being the same pair on all three
cores -- `c2_arm_tail_is_break` 51/49 j1 t16 and `c6_both_arms_end_in_raise` 46/52 j4 t19,
i.e. pre-existing defects of other families, NOT regressions caused here.  The shipping
criterion for this file is therefore sha-level: its product is byte-identical head vs R31-C
(`SAME` in the A/B), which is what proves the predicate does not fire on any of the six
neighbour positions.
"""
''',
}


def split_header(text):
    if text.startswith('#'):
        text = text.split('\n', 1)[1]
    assert text.startswith('"""'), text[:20]
    end = text.index('"""', 3) + 3
    body = text[end:]
    assert body.lstrip('\n').startswith(('def ', 'import ', 'from ')), body[:40]
    return body


def main():
    apply = '--apply' in sys.argv
    for name in NAMES:
        src = io.open(os.path.join(SRC, name), encoding='utf-8').read()
        body = split_header(src)
        head = HEADERS[name]
        assert head.startswith('# -*- coding: utf-8 -*-'), head[:30]
        out = (head + body).replace('\r\n', '\n')
        assert '\r' not in out
        crlf = out.replace('\n', '\r\n').encode('utf-8')
        dst = os.path.join(DST, name)
        print('%s -> %s  (%d bytes, %d CRLF, body %d chars unchanged)'
              % (name, dst, len(crlf), crlf.count(b'\r\n'), len(body)))
        if not apply:
            continue
        if not os.path.isdir(DST):
            os.makedirs(DST)
        io.open(dst, 'wb').write(crlf)
        pyc = dst[:-3] + '.pyc'
        py_compile.compile(dst, cfile=pyc, doraise=True)
        chk = io.open(dst, 'rb').read()
        assert chk == crlf and chk.count(b'\r\n') == chk.count(b'\n')
        assert os.path.getsize(pyc) > 200, pyc
    if not apply:
        print('dry run')


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
