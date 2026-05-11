import py_compile, sys, os, marshal, json
sys.path.insert(0, r'd:\Desktop\ptrade相关\pythoncdc')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_ast_generator import RegionASTGenerator

tf = 'test_w03_multi_with.py'
pyc = tf+'c'
py_compile.compile(tf, cfile=pyc, doraise=True)
with open(pyc, 'rb') as f:
    f.read(16)
    code = marshal.load(f)
func_code = code.co_consts[0]
cfg = CFGBuilder().build(func_code)

gen = RegionASTGenerator(cfg, top_level_code=func_code)
ast = gen.generate()

body = ast.get('body', [])
print(f'Total body statements: {len(body)}')
for i, node in enumerate(body):
    t = node.get('type', '?') if isinstance(node, dict) else str(node)
    print(f'  [{i}] {t}')

if os.path.exists(pyc): os.remove(pyc)
