"""R29 测试工程师：检查多个失败函数的if-elif chain merge_block问题"""
import sys
sys.path.insert(0, '/workspace')

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
from core.pyc_loader_v2 import load_pyc_file_v2
import types

PYC = '/workspace/quotation.pyc'

module = load_pyc_file_v2(PYC)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

# 收集所有code objects
def walk(co, prefix=''):
    name = prefix + co.co_name if prefix else co.co_name
    if co.co_name == '<module>' and not prefix:
        name = '<module>'
    yield name, co
    for const in co.co_consts:
        if isinstance(const, types.CodeType):
            sub_prefix = name + '.' if name != '<module>' else ''
            yield from walk(const, sub_prefix)

all_codes = dict(walk(code_obj))

# 检查这些失败函数
TARGETS = ['get_fields', 'get_option_info', 'get_cb_time_info', 'change_his_to_forward',
           'get_block_stocks', 'fill_minute_or_day_blank', 'load_get_price', 'valuation_new',
           'get_valuation_new', 'build_future_fill_time', 'get_date_and_count']

for name in TARGETS:
    if name not in all_codes:
        continue
    co = all_codes[name]
    builder = CFGBuilder()
    cfg = builder.build(co)
    analyzer = RegionAnalyzer(cfg)
    regions = analyzer.analyze()

    # 找到最外层的IfRegion
    outer_ifs = [r for r in regions if type(r).__name__ == 'IfRegion'
                 and r.entry.start_offset == 0
                 and hasattr(r, 'merge_block') and r.merge_block]

    # 检查是否有then_blocks包含JUMP_FORWARD目标的情况
    print(f"\n=== {name} ===")
    for r in regions:
        if type(r).__name__ != 'IfRegion':
            continue
        if not hasattr(r, 'merge_block') or not r.merge_block:
            continue
        # 检查then_blocks中是否有块以JUMP_FORWARD结尾
        then_jumps = []
        for b in r.then_blocks:
            last = b.get_last_instruction()
            if last and last.opname == 'JUMP_FORWARD':
                then_jumps.append((b.start_offset, last.argval))

        if then_jumps:
            merge_off = r.merge_block.start_offset
            # 检查JUMP_FORWARD目标是否与merge_block一致
            all_same = all(t == merge_off for _, t in then_jumps)
            # 检查then_blocks是否包含了非then块
            then_block_offsets = {b.start_offset for b in r.then_blocks}
            merge_in_then = merge_off in then_block_offsets

            if not all_same or merge_in_then:
                print(f"  IfRegion@{r.entry.start_offset}: merge={merge_off}")
                print(f"    then_jumps: {then_jumps}")
                print(f"    all_jump_to_merge: {all_same}, merge_in_then: {merge_in_then}")
                print(f"    then_blocks: {[b.start_offset for b in r.then_blocks]}")
