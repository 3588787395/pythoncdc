"""R16 调试：dump check_frequency 的完整字节码和CFG区域。"""
import sys
import types
import marshal
import dis

sys.path.insert(0, '/workspace')

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
    code = pyc_codes['<module>.check_frequency']
    print("=== check_frequency 字节码 ===")
    for ins in dis.get_instructions(code):
        print(f"  {ins.offset:4d} {ins.opname:25s} {repr(ins.argval)}")

    print("\n=== CFG 和区域分析 ===")
    from core.cfg import build_cfg
    from core.cfg.region_analyzer import RegionAnalyzer

    cfg = build_cfg(code)
    analyzer = RegionAnalyzer(cfg)
    analyzer.analyze()

    print(f"\n区域数: {len(analyzer.regions)}")
    for r in analyzer.regions:
        print(f"  {type(r).__name__}: entry={r.entry.start_offset if r.entry else None}")
        if hasattr(r, 'condition_block') and r.condition_block:
            print(f"    condition_block={r.condition_block.start_offset}")
        if hasattr(r, 'message_block') and r.message_block:
            print(f"    message_block={r.message_block.start_offset}")
        if hasattr(r, 'try_blocks') and r.try_blocks:
            print(f"    try_blocks={[b.start_offset for b in r.try_blocks]}")
        if hasattr(r, 'else_blocks') and r.else_blocks:
            print(f"    else_blocks={[b.start_offset for b in r.else_blocks]}")


if __name__ == '__main__':
    main()
