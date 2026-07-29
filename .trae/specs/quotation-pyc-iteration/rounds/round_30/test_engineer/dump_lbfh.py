"""Dump load_bars_from_hundsun pyc instructions with block structure."""
import sys
import dis
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer

PYC = '/workspace/quotation.pyc'


def load_code(pyc_path):
    module = load_pyc_file_v2(pyc_path)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()
    for c in code_obj.co_consts:
        if isinstance(c, type(code_obj)) and c.co_name == 'load_bars_from_hundsun':
            return c
    return None


def main():
    co = load_code(PYC)
    if co is None:
        print("NOT FOUND")
        return
    print(f"=== load_bars_from_hundsun: {len(co.co_code)} bytes ===")
    print(f"co_consts: {co.co_consts}")
    print(f"co_names: {co.co_names}")
    print(f"co_varnames: {co.co_varnames}")
    print()
    print("=== Full disassembly ===")
    for ins in dis.get_instructions(co):
        argval = ins.argval
        if isinstance(argval, type(co)):
            argval = f'<code {argval.co_name}>'
        arg_disp = ins.arg if ins.arg is not None else ''
        print(f"  {ins.offset:4d} {ins.opname:30s} {arg_disp} {argval}")

    print()
    print("=== CFG blocks ===")
    cfg = build_cfg(co)
    blocks = list(cfg.blocks.values()) if isinstance(cfg.blocks, dict) else list(cfg.blocks)
    blocks.sort(key=lambda b: b.start_offset)
    for b in blocks:
        last = b.instructions[-1] if b.instructions else None
        last_str = f"{last.opname} {last.argval}" if last else "None"
        succs = [s.start_offset for s in b.successors]
        print(f"  block {b.start_offset:4d} id={b.id:3d} succs={succs} last={last_str}")
        for ins in b.instructions:
            argval = ins.argval
            if isinstance(argval, type(co)):
                argval = f'<code {argval.co_name}>'
            print(f"      {ins.offset:4d} {ins.opname:25s} {argval}")

    print()
    print("=== Region structure ===")
    ra = RegionAnalyzer(cfg)
    ra.analyze()
    if hasattr(ra, 'regions'):
        for r in ra.regions:
            entry = getattr(r, 'entry_block', None) or getattr(r, 'condition_block', None) or getattr(r, 'header_block', None)
            eo = entry.start_offset if entry is not None else None
            rtype = getattr(r, 'region_type', type(r).__name__)
            then_blks = [b.start_offset for b in getattr(r, 'then_blocks', [])]
            else_blks = [b.start_offset for b in getattr(r, 'else_blocks', [])]
            merge_blk = getattr(r, 'merge_block', None)
            merge_off = merge_blk.start_offset if merge_blk is not None else None
            body_blks = [b.start_offset for b in getattr(r, 'body_blocks', [])]
            print(f"  region type={rtype} entry={eo} then={then_blks} else={else_blks} merge={merge_off} body={body_blks}")
    elif hasattr(ra, 'root_region'):
        root = ra.root_region
        print(f"  root region: {root}")
    elif hasattr(ra, 'root'):
        print(f"  root: {ra.root}")


if __name__ == '__main__':
    main()
