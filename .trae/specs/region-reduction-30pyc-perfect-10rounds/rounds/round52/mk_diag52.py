# -*- coding: utf-8 -*-
"""Build an instrumented mirror core that names every site appending a Continue statement.

The generator is 3 MB / CRLF / BOM, so patching by line number is far safer than by anchor text.
"""
import io
import os
import re
import shutil
import sys

REPO = r'F:\Downloads\pythoncdc-main'
ROOT = r'D:/Temp/r52gate'
REL = 'core/cfg/region_ast_generator.py'
DST = ROOT + '/mirr_diag'
SRC = os.path.join(REPO, REL.replace('/', os.sep))
sys.stdout.reconfigure(encoding='utf-8')

PAT = re.compile(r"^(\s*)(?:[\w\.\[\]'\"]+(?:\+ |\s*)*= |\S.*?\.append\()?.*\{'type': 'Continue'\}.*$")

if os.path.isdir(DST):
    shutil.rmtree(DST)
os.makedirs(DST)
shutil.copytree(os.path.join(REPO, 'core'), os.path.join(DST, 'core'),
                ignore=shutil.ignore_patterns('__pycache__'))
assert not [d for d, _, _ in os.walk(os.path.join(DST, 'core')) if d.endswith('__pycache__')]
shutil.copy(os.path.join(REPO, 'pycdc.py'), os.path.join(DST, 'pycdc.py'))

raw = io.open(SRC, 'rb').read()
assert raw[:3] == b'\xef\xbb\xbf', 'unexpected: no BOM'
assert raw.count(b'\n') == raw.count(b'\r\n'), 'mixed endings in source'
text = raw.decode('utf-8-sig')
lines = text.split('\r\n')

sites = []
out = []
# Only whole-line, self-contained statements may take a trailing insertion: a dict-literal
# fragment such as `'body': [{'type': 'Continue'}],` would break the enclosing expression.
SELF_CONTAINED = re.compile(
    r"^\s*(?:[\w\.]+\.append\(\{'type': 'Continue'\}\)"
    r"|[\w\.]+ = \[\{'type': 'Continue'\}\]"
    r"|return \[\{'type': 'Continue'\}\])\s*$")
for n, ln in enumerate(lines, 1):
    if SELF_CONTAINED.match(ln):
        ind = re.match(r'^(\s*)', ln).group(1)
        sites.append(n)
        out.append(ind + "print('CONT-SITE " + str(n) + " depth=' + str(self._loop_depth)"
                   " + ' blk=' + str(getattr(locals().get('block'), 'start_offset', None))"
                   " + ' regs=' + str(getattr(locals().get('region'), 'entry', None)), flush=True)")
    out.append(ln)

new = '\r\n'.join(out)
io.open(os.path.join(DST, REL.replace('/', os.sep)), 'w',
        encoding='utf-8-sig', newline='').write(new)
chk = io.open(os.path.join(DST, REL.replace('/', os.sep)), 'rb').read()
assert chk.count(b'\n') == chk.count(b'\r\n'), 'mixed endings after patch'
import py_compile
py_compile.compile(os.path.join(DST, REL.replace('/', os.sep)), doraise=True, quiet=2)
print('instrumented %d sites -> %s' % (len(sites), DST))
print('sites:', sites)
