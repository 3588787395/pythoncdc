import sys, marshal, types
sys.stdout.reconfigure(encoding='utf-8')
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
cfg = build_cfg(co)

# Patch to trace when block 2094 is added to and removed from generated_blocks
import core.cfg.region_ast_generator as rag

_orig_gen = rag.RegionASTGenerator.generate
class PatchedSet:
    def __init__(self, original_set, label):
        self._set = original_set
        self._label = label
    def add(self, item):
        if hasattr(item, 'start_offset') and item.start_offset == 2094:
            import traceback
            print(f'[TRACE] {self._label}.add(block@2094)')
            for line in traceback.format_stack()[-5:-1]:
                print(f'  {line.strip()}')
        self._set.add(item)
    def discard(self, item):
        if hasattr(item, 'start_offset') and item.start_offset == 2094:
            import traceback
            print(f'[TRACE] {self._label}.discard(block@2094)')
            for line in traceback.format_stack()[-5:-1]:
                print(f'  {line.strip()}')
        self._set.discard(item)
    def remove(self, item):
        if hasattr(item, 'start_offset') and item.start_offset == 2094:
            import traceback
            print(f'[TRACE] {self._label}.remove(block@2094)')
        self._set.remove(item)
    def __contains__(self, item):
        return item in self._set
    def __iter__(self):
        return iter(self._set)
    def __bool__(self):
        return bool(self._set)
    def update(self, items):
        for item in items:
            self.add(item)
    def __len__(self):
        return len(self._set)

gen = RegionASTGenerator(cfg, top_level_code=None)
gen.generated_blocks = PatchedSet(gen.generated_blocks, 'generated_blocks')
ast_dict = gen.generate()
