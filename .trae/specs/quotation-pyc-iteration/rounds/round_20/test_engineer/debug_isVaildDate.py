"""R20 测试工程师：调试 isVaildDate 的 try-except post-try 代码丢失"""
import sys
import types
import traceback

sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2

PYC = '/workspace/quotation.pyc'


def load_pyc_code_objects(pyc_path):
    module = load_pyc_file_v2(pyc_path)
    if not module:
        return {}
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()
    result = {}
    def walk(co, prefix=''):
        name = prefix + co.co_name if prefix else co.co_name
        if co.co_name == '<module>' and not prefix:
            name = '<module>'
        result[name] = co
        for const in co.co_consts:
            if isinstance(const, types.CodeType):
                sub_prefix = name + '.' if name != '<module>' else ''
                walk(const, sub_prefix)
    walk(code_obj)
    return result


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    name = 'isVaildDate'
    co = pyc_codes[name]
    print(f"=== {name} ===")

    from core.cfg.cfg_builder import CFGBuilder
    from core.cfg.region_analyzer import RegionAnalyzer, TryExceptRegion, IfRegion

    cfg = CFGBuilder().build(co)
    blocks = cfg.blocks
    for k in sorted(blocks.keys()):
        b = blocks[k]
        print(f"  block {k} (start {b.start_offset}): succs={[s.id for s in b.successors]} preds={[p.id for p in b.predecessors]}")
        for i in b.instructions:
            print(f"    {i.offset:4d} {i.opname:30s} {i.argval!r}")

    print()
    analyzer = RegionAnalyzer(cfg)
    regions = analyzer.analyze()

    # Find TryExceptRegion
    for r in regions:
        if isinstance(r, TryExceptRegion):
            print(f"TryExceptRegion: entry={r.entry.id}")
            print(f"  try_blocks={[b.id for b in r.try_blocks]}")
            print(f"  else_blocks={[b.id for b in (r.else_blocks or [])]}")
            print(f"  all blocks={[b.id for b in r.blocks]}")
            print(f"  try_blocks succs: {[(b.id, [s.id for s in b.successors]) for b in r.try_blocks]}")
            print(f"  else_blocks succs: {[(b.id, [s.id for s in b.successors]) for b in (r.else_blocks or [])]}")

    # Check if merge_block of IfRegion matches any successor
    print()
    for r in regions:
        print(f"Region: {type(r).__name__} entry={r.entry.id} blocks={[b.id for b in r.blocks]}")
        if isinstance(r, IfRegion):
            print(f"  merge_block={r.merge_block.id if r.merge_block else None}")


if __name__ == '__main__':
    main()
