# -*- coding: utf-8 -*-
"""Map every landed R64 edit to a landed line number (replay proof of where it went)."""
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
REPO = r'F:/Downloads/pythoncdc-main'
GATE = r'D:/Temp/opencode/r65gate'
CR = chr(13)
MARK = re.compile(r'\[R64[^\]]*\]')

for name in ('full2_region_ast_generator.py.json', 'full2_region_analyzer.py.json'):
    spec = json.load(io.open(os.path.join(GATE, name), encoding='utf-8'))
    rel = spec['file']
    txt = io.open(os.path.join(REPO, rel.replace('/', os.sep)), 'rb').read().decode('utf-8-sig')
    txt = txt.replace(CR + '\n', '\n')
    lines = txt.split('\n')
    print('== %s  (%d edits)' % (rel, len(spec['edits'])))
    for k, e in enumerate(spec['edits']):
        body = [l.strip() for l in e['repl'].split('\n') if len(l.strip()) > 24]
        body.sort(key=len, reverse=True)
        line = -1
        for probe in body[:6]:
            hits = [i + 1 for i, l in enumerate(lines) if probe in l]
            if len(hits) == 1:
                line = hits[0]
                break
        marks = ', '.join(sorted(set(MARK.findall(e['repl'])))) or '(no marker)'
        print('  edit %2d  landed line %-6s  %s  (+%d lines)'
              % (k + 1, line if line > 0 else '?', marks,
                 e['repl'].count('\n') - e['anchor'].count('\n')))
