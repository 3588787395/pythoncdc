# -*- coding: utf-8 -*-
"""Replay the R67-diag5 'pair' arm: generator candidate + analyzer (d') follow-up.

h62.py specs are single-file by contract, so the two-step landing is assembled here:
  1. h62.py build --spec=specs/cand_r67_ccprefix.json --dst=ccp_final   (generator)
  2. python -X utf8 mk_pair.py                                          (adds the analyzer edit)
  3. python -X utf8 h62.py run --arm=pair --list=battery.txt --out=dump/pair_batt.jsonl

Every anchor is asserted count==1 on the bytes it is applied to. Nothing in
F:/Downloads/pythoncdc-main is written.
"""
import io
import json
import os
import shutil
import sys

sys.stdout.reconfigure(encoding='utf-8')
GEN_SPEC = 'specs/cand_r67_ccprefix.json'
ANA_SPEC = 'specs/cand_r67_dsplit_analyzer.json'
SRC = 'mirr_ccp_final'
DST = 'mirr_pair'

assert os.path.isdir(SRC), 'run `python -X utf8 h62.py build --spec=%s --dst=ccp_final` first' % GEN_SPEC
sp = json.load(io.open(ANA_SPEC, encoding='utf-8'))
if os.path.isdir(DST):
    shutil.rmtree(DST)
shutil.copytree(SRC, DST)
path = os.path.join(DST, sp['file'])
raw = io.open(path, encoding='utf-8', newline='').read()
nl = '\r\n' if raw.count('\r\n') else '\n'
u = raw.replace(nl, '\n')
for k, e in enumerate(sp['edits']):
    assert u.count(e['anchor']) == 1, 'edit %d anchor count=%d' % (k, u.count(e['anchor']))
    u = u.replace(e['anchor'], e['repl'])
io.open(path, 'w', encoding='utf-8', newline='').write(u.replace('\n', nl))
g = io.open(os.path.join(DST, 'core/cfg/region_ast_generator.py'),
            encoding='utf-8', newline='').read()
print('pair mirror %s ready: generator helper=%s, callsites=%d, analyzer (d\')=%s, nl=%s'
      % (DST, '_r67_split_cc_ternary_stmt_prefix' in g,
         g.count('self._r67_split_cc_ternary_stmt_prefix(region, pre_stmts)'),
         '_r67_last_zero' in u, 'CRLF' if nl == '\r\n' else 'LF'))
