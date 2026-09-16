import sys, marshal, types, logging
sys.stdout.reconfigure(encoding='utf-8')

# Patch _generate_block_statements_body to add logging
import core.cfg.region_ast_generator as rag
orig_method = rag.RegionASTGenerator._generate_block_statements_body

call_count = [0]
def patched_method(self, block, _cjb_parent=None):
    call_count[0] += 1
    result = orig_method(self, block, _cjb_parent)
    if hasattr(block, 'start_offset') and block.start_offset == 2094:
        b2094 = self.cfg.get_block_by_offset(2094)
        in_gen = b2094 in self.generated_blocks
        last = block.instructions[-1] if block.instructions else None
        print(f'[DEBUG] _generate_block_statements_body called for block 2094:')
        print(f'  last_instr: {last.opname if last else None}')
        print(f'  result: {result}')
        print(f'  in generated_blocks after: {in_gen}')
        # Check if F-GET_ITER guard fired
        from core.cfg.region_analyzer import LoopRegion
        for _lr in self.region_analyzer.regions:
            if isinstance(_lr, LoopRegion):
                _fis = _lr.metadata.get('for_iter_setup')
                if _fis is block:
                    h = _lr.header_block
                    h_off = h.start_offset if hasattr(h, 'start_offset') else None
                    gen_id = id(_lr) in self._generated_regions
                    print(f'  LoopRegion@{h_off} for_iter_setup=2094, generated={gen_id}')
    return result

rag.RegionASTGenerator._generate_block_statements_body = patched_method

pyc = 'F:/Downloads/pythoncdc-main/site-packages/IQData/plugins/plugin_system_local_finance/finance_data_source.pyc'
with open(pyc, 'rb') as f:
    f.read(16); orig = marshal.load(f)
def extract(co):
    r = {}; r[co.co_name or '<module>'] = co
    for c in co.co_consts:
        if isinstance(c, types.CodeType): r.update(extract(c))
    return r
om = extract(orig)
co = om['growth_factors_sql_get']
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.ast_converter import CFGASTConverter
from core.cfg.code_generator import CFGCodeGenerator
cfg = build_cfg(co)
gen = RegionASTGenerator(cfg, top_level_code=None)
ast_dict = gen.generate()
converter = CFGASTConverter()
py_ast = converter.convert(ast_dict)
code_gen = CFGCodeGenerator()
source = code_gen.generate(py_ast)
print(f'\nTotal calls to _generate_block_statements_body: {call_count[0]}')
