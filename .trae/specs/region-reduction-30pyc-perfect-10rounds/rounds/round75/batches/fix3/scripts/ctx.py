# -*- coding: utf-8 -*-
"""ctx.py <arm> <pyc> <func> <block>... : show preds + their successors' last ops."""
import importlib.util, io, marshal, os, sys
sys.stdout.reconfigure(encoding='utf-8')
CENTER = r'D:\Temp\opencode\r75gate\center'
arm, pyc, func = sys.argv[1], sys.argv[2], sys.argv[3]
s = importlib.util.spec_from_file_location('h62x', os.path.join(CENTER, 'h62.py'))
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
pycdc = m._load_arm(arm)
from core.cfg import build_cfg
code = marshal.loads(io.open(pyc, 'rb').read()[16:])
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
    print('== block %s ==' % arg)
    for p in sorted(b.predecessors, key=lambda x: x.start_offset):
        li = p.get_last_instruction()
        succ = []
        for s2 in sorted(p.successors, key=lambda x: x.start_offset):
            sl = s2.get_last_instruction()
            succ.append('%d:%s' % (s2.start_offset, sl.opname if sl else '?'))
        print('   pred %d last=%s succs=[%s]' % (p.start_offset, li.opname if li else None, ', '.join(succ)))
