import sys, marshal, types, linecache
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')
import core.cfg.region_analyzer as ra
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer

SRC_FILE = ra.__file__.replace('\\', '/')
mc = marshal.loads(open(r'D:\temp\opencode\cl_layout\fi\fi1.pyc','rb').read()[16:])
fnc = [k for k in mc.co_consts if isinstance(k, types.CodeType) and k.co_name=='find'][0]

hits = []
def tracer(frame, event, arg):
    if event != 'line':
        return tracer
    co = frame.f_code
    if co.co_name != '_identify_conditional_regions':
        return tracer
    ln = frame.f_lineno
    src = linecache.getline(SRC_FILE, ln).strip()
    if src.startswith('merge = ') or src.startswith('merge=') or src.startswith('merge ='):
        off = None
        for nm in ('block','then_succ','else_succ','merge'):
            v = frame.f_locals.get(nm)
            o = getattr(v, 'start_offset', None) if v is not None else None
            if nm == 'block': off = o
        hits.append((ln, off, src[:70], frame.f_locals.get('then_succ') and frame.f_locals['then_succ'].start_offset, frame.f_locals.get('else_succ') and frame.f_locals['else_succ'].start_offset))
    return tracer

cfg = build_cfg(fnc, name='find')
an = RegionAnalyzer(cfg, parent_code=fnc)
sys.settrace(tracer)
an.analyze()
sys.settrace(None)
for h in hits:
    print('L%d block=%s then=%s else=%s | %s' % (h[0], h[1], h[3], h[4], h[2]))
