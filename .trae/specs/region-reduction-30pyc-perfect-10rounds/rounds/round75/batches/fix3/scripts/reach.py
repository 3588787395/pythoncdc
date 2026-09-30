# -*- coding: utf-8 -*-
import importlib.util, io, marshal, os, sys
sys.stdout.reconfigure(encoding='utf-8')
CENTER = r'D:\Temp\opencode\r75gate\center'
arm, pyc, func, then_off, else_off = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
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
t = cfg.get_block_by_offset(then_off); e = cfg.get_block_by_offset(else_off)
seen=set(); stack=[t]
while stack:
    b=stack.pop()
    if b in seen: continue
    seen.add(b)
    for s2 in (b.successors or []):
        exc = getattr(b,'exception_successors',None) or set()
        if s2 not in exc: stack.append(s2)
print('then=%d else=%d reachable_from_then=%s' % (then_off, else_off, e in seen))
