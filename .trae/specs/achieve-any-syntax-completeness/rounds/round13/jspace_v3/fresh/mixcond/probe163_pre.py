# -*- coding: utf-8 -*-
"""probe163_pre: 追踪 mx1 中 For 前 Expr(Iter(attrs)) 由 _loop_generate_for 的哪个 pre_stmts 来源产生。"""
import sys, marshal, types
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator

path, want = sys.argv[1], sys.argv[2]

def load(p):
    return marshal.loads(open(p, 'rb').read()[16:])

def walk(co, prefix=''):
    yield prefix + co.co_name, co
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            yield from walk(c, prefix + co.co_name + '.')

co = None
for name, c in walk(load(path)):
    if c.co_name == want:
        co = c
        break
cfg = build_cfg(co)
gen = RegionASTGenerator(cfg)

orig_ext = gen._loop_extract_for_iter_pre_stmts
def ext_wrap(instrs, block):
    pre, rem = orig_ext(instrs, block)
    print(f'[extract] block@{block.start_offset} instrs={[i.opname for i in instrs]}')
    print(f'          pre={pre}')
    print(f'          rem={[i.opname for i in rem]}')
    return pre, rem
gen._loop_extract_for_iter_pre_stmts = ext_wrap

orig_for = gen._loop_generate_for
def for_wrap(region):
    res = orig_for(region)
    print(f'[loop] entry@{region.entry.start_offset} pre_stmts={res.get("pre_stmts")}')
    return res
gen._loop_generate_for = for_wrap

orig_build_stmt = gen._build_statement
def build_wrap(instrs, *a, **k):
    r = orig_build_stmt(instrs, *a, **k)
    if isinstance(r, dict) and r.get('type') == 'Expr' and isinstance(r.get('value'), dict) \
            and r['value'].get('type') == 'Iter':
        import traceback
        frames = traceback.extract_stack()
        print(f'[build_statement] Iter-Expr from {[i.opname for i in instrs]}')
        for fr in frames[-7:-1]:
            print(f'    {fr.filename.split(chr(92))[-1]}:{fr.lineno} {fr.name} :: {fr.line[:100] if fr.line else ""}')
    return r
gen._build_statement = build_wrap

ast = gen.generate()
print('BODY:', [s.get('type') for s in ast.get('body', [])])
