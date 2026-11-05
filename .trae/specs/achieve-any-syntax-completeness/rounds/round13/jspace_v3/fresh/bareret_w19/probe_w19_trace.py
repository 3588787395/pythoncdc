# rr-v5r115 探针 3b：settrace 行级追踪 BSS-body(96)（帧作用域收紧）
import sys, os
REPO = 'F:/Downloads/pythoncdc-main'
sys.path.insert(0, REPO)
os.chdir(REPO)
from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg import build_cfg
from core.cfg import region_ast_generator as rag

module = load_pyc_file_v2('D:/temp/opencode/cl_layout/r115diag/repro4.pyc')
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
root = code_obj.to_python_code() if hasattr(code_obj, 'to_python_code') else code_obj
def find_code(code, acc):
    for c in code.co_consts:
        if hasattr(c, 'co_name'):
            acc.append(c); find_code(c, acc)
acc = []
find_code(root, acc)
m = [c for c in acc if c.co_name == 'm'][0]
cfg = build_cfg(m)

src_lines = open(os.path.normpath(REPO + '/core/cfg/region_ast_generator.py'), encoding='utf-8').read().splitlines()
events = []
active = set()  # frames of interest

def tracer(frame, event, arg):
    co = frame.f_code
    if os.path.normpath(co.co_filename) != os.path.normpath(REPO + '/core/cfg/region_ast_generator.py'):
        return None if not active else tracer
    fn = co.co_name
    if event == 'call':
        if fn == '_generate_block_statements_body':
            b = frame.f_locals.get('block')
            if b is not None and getattr(b, 'start_offset', None) == 96:
                active.add(id(frame))
                events.append(('enter-bssb96', frame.f_lineno))
                return tracer
            return tracer  # 其他 bss-body 调用继续跟（不记录）
        if id(frame) in active or any(True for _ in ()):
            pass
        # 在 96 帧活跃期间进入的子调用也记录
        return tracer
    if event == 'return':
        active.discard(id(frame))
        return None
    if event == 'line' and active:
        # 只记录当前帧属于 96 作用域的行
        f = frame
        while f is not None:
            if id(f) in active:
                events.append(('line', frame.f_lineno))
                break
            f = f.f_back
        return tracer
    return tracer if active else None

gen = rag.RegionASTGenerator(cfg, top_level_code=None)
sys.settrace(tracer)
try:
    gen.generate()
finally:
    sys.settrace(None)

out = []
prev = None
for kind, x in events:
    if kind == 'enter-bssb96':
        out.append('=== ENTER BSS-body(96) ===')
        prev = None
        continue
    if x != prev:
        out.append('%5d: %s' % (x, src_lines[x-1].strip()[:105]))
    prev = x
print('steps:', len(out))
print('\n'.join(out[-70:]))
