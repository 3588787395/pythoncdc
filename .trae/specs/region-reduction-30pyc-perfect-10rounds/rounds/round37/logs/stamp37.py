# -*- coding: utf-8 -*-
"""Round 37 causal probe: run the LANDED core (R37-A present) over the corpus target and print,
at the exact patched site, every donor-chain candidate the new `continue` rejects — together with
whether the pre-R37-A offset test would have accepted it.

  python -X utf8 stamp37.py            # writes g0_stamp_strategy.txt (stderr) into this dir

The core under test is a stamped COPY of mirr_r37a (mirr_stamp37) so the measured arm stays
pristine; the repo core is never edited.
"""
import io
import os
import shutil
import subprocess
import sys

SCR = r'D:/Temp/r37gate/r37'
SRC = os.path.join(SCR, 'mirr_r37a')
DST = os.path.join(SCR, 'mirr_stamp37')
REL = os.path.join('core', 'cfg', 'region_ast_generator.py')

OLD = (u"                    _r37_rb = set(getattr(r, 'blocks', None) or [])\r\n"
       u"                    if region.entry is not None and region.entry in _r37_rb:\r\n"
       u"                        continue        # [R37-A] an ancestor chain may not lend its elif arms\r\n")
NEW = (u"                    _r37_rb = set(getattr(r, 'blocks', None) or [])\r\n"
       u"                    if region.entry is not None and region.entry in _r37_rb:\r\n"
       u"                        import sys as _s37\r\n"
       u"                        if any(b.start_offset == _r23_or_then.start_offset\r\n"
       u"                                 for b in r.then_blocks):\r\n"
       u"                            print('[STAMP37] REJECT donor entry=%r donor_blocks=%d "
       u"cur_entry=%r would_have_been_accepted=True' % (\r\n"
       u"                                getattr(r.entry, 'start_offset', None), len(_r37_rb),\r\n"
       u"                                getattr(region.entry, 'start_offset', None)),\r\n"
       u"                                file=_s37.stderr, flush=True)\r\n"
       u"                        continue        # [R37-A] an ancestor chain may not lend its elif arms\r\n")

if os.path.isdir(DST):
    shutil.rmtree(DST)
shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns('__pycache__'))
p = os.path.join(DST, REL)
raw = io.open(p, 'rb').read()
assert raw.count(OLD.encode('utf-8')) == 1, 'anchor not unique in stamped copy: %d' % raw.count(OLD.encode('utf-8'))
open(p, 'wb').write(raw.replace(OLD.encode('utf-8'), NEW.encode('utf-8'), 1))
print('stamped copy ready: %s' % p)

PYC = (r'F:\Downloads\pythoncdc-main\site-packages\IQEngine\plugins'
       r'\plugin_fly_data\strategy\strategy.pyc')
driver = (
    "import sys, io, os\n"
    "sys.path.insert(0, %r)\n"
    "sys.path.append(%r)\n"
    "import pycdc\n"
    "assert os.path.dirname(os.path.abspath(pycdc.__file__)).replace(chr(92),'/') == %r, pycdc.__file__\n"
    "src = pycdc.decompile_pyc(%r)\n"
    "io.open(%r, 'w', encoding='utf-8', newline='').write(src or '')\n"
    "print('product bytes', len((src or '').encode('utf-8')))\n"
) % (DST, r'F:\Downloads\pythoncdc-main', DST.replace('\\', '/'), PYC,
     os.path.join(SCR, 'stamp37_strategyOK.py'))

r = subprocess.run([sys.executable, '-X', 'utf8', '-c', driver],
                   cwd=SCR, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
out = r.stdout.decode('utf-8', 'replace')
io.open(os.path.join(SCR, 'g0_stamp_strategy.txt'), 'w', encoding='utf-8', newline='\n').write(out)
hits = [l for l in out.splitlines() if 'STAMP37' in l]
print('rc=%d  stamp lines=%d' % (r.returncode, len(hits)))
for h in hits[:20]:
    print(' ', h)
print(out.splitlines()[-1] if out.strip() else '(no output)')
