import sys
sys.path.insert(0, '.')
import marshal

pyc_path = 'site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc'
with open(pyc_path, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.cfg_builder import build_cfg
from core.cfg.ast_converter import CFGASTConverter
from core.cfg.code_generator import CodeGenerator

def process_code(code_obj):
    cfg = build_cfg(code_obj)
    gen = RegionASTGenerator(cfg)
    ast_dict = gen.generate()
    converter = CFGASTConverter()
    py_ast = converter.convert(ast_dict)
    generator = CodeGenerator()
    result = generator.generate(py_ast)
    return result

result = process_code(code)
lines = result.split('\n')
# Find all while loops and show them
i = 0
count = 0
while i < len(lines) and count < 200:
    stripped = lines[i].strip()
    if stripped.startswith('while '):
        for j in range(i, min(i+20, len(lines))):
            print(f'{j+1}: {lines[j]}')
        print('===')
        count += 20
    i += 1
