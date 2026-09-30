# -*- coding: utf-8 -*-
"""preds.py <arm> <pyc> <func> <block>... : print each block's predecessors + last op."""
import importlib.util, io, marshal, os, sys
sys.stdout.reconfigure(encoding='utf-8')
CENTER = r'D:\Temp\opencode\r75gate\center'
arm, pyc, func = sys.argv[1], sys.argv[2], sys.argv[3]
s = importlib.util.spec_from_file_location('h62x', os.path.join(CENTER, 'h62.py'))
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
pycdc = m._load_arm(arm)
from core.cfg import build_cfg
code = marshal.loads(io.open(pyc,'rb').read()[16:])
def find(c, name):
    for k in c.co_consts:
        if hasattr(k, 'co_code'):
            if k.co_name == name: return k
            r = find(k, name)
            if r: return r
    return None
target = find(code, func) if func != '<module>' else code
cfg = build_cfg(target)
for arg in sys.argv[4:]:
    b = cfg.get_block_by_offset(int(arg))
    if b is None:
        print('block %s NOT FOUND' % arg); continue
    preds = sorted(p.start_offset for p in b.predecessors)
    pred_ops = []
    for p in sorted(b.predecessors, key=lambda x: x.start_offset):
        li = p.get_last_instruction()
        pred_ops.append('%d:%s' % (p.start_offset, li.opname if li else '?'))
    li = b.get_last_instruction()
    print('block %s last=%s preds=[%s]' % (arg, li.opname if li else None, ', '.join(pred_ops)))
