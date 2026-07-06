import py_compile, sys, os, marshal
sys.path.insert(0, r'd:\Desktop\ptrade相关\pythoncdc')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.region_analyzer import RegionAnalyzer

tf = 'test_w03_multi_with.py'
pyc = tf+'c'
py_compile.compile(tf, cfile=pyc, doraise=True)
with open(pyc, 'rb') as f:
    f.read(16)
    code = marshal.load(f)
func_code = code.co_consts[0]
cfg = CFGBuilder().build(func_code)
ra = RegionAnalyzer(cfg)
ra.analyze()

gen = RegionASTGenerator(cfg, top_level_code=func_code)

for b in sorted(cfg.blocks.values(), key=lambda b: b.start_offset):
    if b.start_offset >= 390:
        print(f'\nBlock {b.start_offset} instructions:')
        for i in b.instructions:
            if i.opname != 'CACHE':
                print(f'  {i.offset}: {i.opname} {i.argval}')
        stmts = gen._generate_block_statements(b)
        print(f'Generated {len(stmts)} statements:')
        for s in stmts:
            t = s.get('type', '?')
            if t == 'Assign':
                tgt = s.get('targets', [{}])[0]
                tgt_id = tgt.get('id', '?') if isinstance(tgt, dict) else '?'
                print(f'  Assign: {tgt_id}')
            elif t == 'Return':
                print(f'  Return')
            elif t == 'Expr':
                print(f'  Expr')
            else:
                print(f'  {t}')

if os.path.exists(pyc): os.remove(pyc)
