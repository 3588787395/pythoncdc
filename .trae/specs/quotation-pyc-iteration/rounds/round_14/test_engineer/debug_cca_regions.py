"""R14 调试：显示 cash_collection_ability 的区域结构。"""
import sys
import types
import marshal
import dis

sys.path.insert(0, '/workspace')

from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, TernaryRegion, IfRegion, LoopRegion, BoolOpRegion

PYC = '/workspace/quotation.pyc'


def load_pyc_code_objects(pyc_path):
    with open(pyc_path, 'rb') as f:
        f.read(16)
        code = marshal.load(f)
    result = {}
    _collect(code, result, prefix='')
    return result


def _collect(code, result, prefix):
    if not prefix:
        name = '<module>'
    else:
        name = prefix + '.' + code.co_name
    result[name] = code
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            _collect(c, result, name)


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    code = pyc_codes['<module>.cash_collection_ability']

    cfg = build_cfg(code)

    analyzer = RegionAnalyzer(cfg)
    regions = analyzer.analyze()

    print(f"\n=== cash_collection_ability regions ({len(regions)}) ===")
    for r in regions:
        print(f"\n  {type(r).__name__} (region_type={r.region_type})")
        print(f"    entry={r.entry.start_offset if r.entry else None}")
        if hasattr(r, 'condition_block') and r.condition_block:
            print(f"    condition_block={r.condition_block.start_offset}")
            _ci = [i for i in r.condition_block.instructions if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
            print(f"    condition_block_instrs={[(i.opname, repr(i.argval)[:30]) for i in _ci[-3:]]}")
        if hasattr(r, 'true_value_block') and r.true_value_block:
            print(f"    true_value_block={r.true_value_block.start_offset}")
            _ti = [i for i in r.true_value_block.instructions if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
            print(f"    true_value_block_instrs={[(i.opname, repr(i.argval)[:30]) for i in _ti]}")
        if hasattr(r, 'false_value_block') and r.false_value_block:
            print(f"    false_value_block={r.false_value_block.start_offset}")
            _fi = [i for i in r.false_value_block.instructions if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
            print(f"    false_value_block_instrs={[(i.opname, repr(i.argval)[:30]) for i in _fi]}")
        if hasattr(r, 'merge_block') and r.merge_block:
            print(f"    merge_block={r.merge_block.start_offset}")
        if hasattr(r, 'then_blocks'):
            print(f"    then_blocks={[b.start_offset for b in r.then_blocks]}")
            _eb = getattr(r, 'else_blocks', None) or []
            print(f"    else_blocks={[b.start_offset for b in _eb]}")
        if hasattr(r, 'blocks'):
            print(f"    blocks={[b.start_offset for b in r.blocks]}")
        if hasattr(r, 'elif_conditions'):
            print(f"    elif_conditions={[b.start_offset for b in r.elif_conditions]}")


if __name__ == '__main__':
    main()
