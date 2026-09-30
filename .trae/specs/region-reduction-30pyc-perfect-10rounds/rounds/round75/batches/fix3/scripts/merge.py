# -*- coding: utf-8 -*-
"""merge.py <out.json> <in1.json> <in2.json> ...   合并同文件多份 spec 为一份。"""
import io
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
out = sys.argv[1]
specs = [json.load(io.open(p, encoding='utf-8')) for p in sys.argv[2:]]
files = {s['file'] for s in specs}
assert len(files) == 1, files
edits = []
for s in specs:
    edits.extend(s.get('edits') or [{'anchor': s['anchor'], 'repl': s['repl']}])
json.dump({'file': specs[0]['file'], 'edits': edits},
          io.open(out, 'w', encoding='utf-8', newline='\n'),
          ensure_ascii=False, indent=1)
print('merged %d spec(s) -> %s edits=%d file=%s'
      % (len(specs), out, len(edits), specs[0]['file']))
