#!/usr/bin/env python3
"""打印函数内每个基本块的 BlockRole、所属 region 与指令。"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _find_root(start: Path) -> Path:
    for p in [start] + list(start.parents):
        if (p / 'core' / 'cfg').is_dir() and (p / 'pycdc.py').is_file():
            return p
    raise RuntimeError(start)


ROOT = _find_root(HERE)
sys.path.insert(0, str(ROOT))

from core.cfg import build_cfg  # noqa: E402
from core.cfg.region_analyzer import RegionAnalyzer  # noqa: E402


def dump_code(co, indent=''):
    cfg = build_cfg(co)
    ra = RegionAnalyzer(cfg)
    regions = ra.analyze()
    print(f'{indent}==== code object {co.co_name} ====')
    role_of = {}
    for b in cfg.get_blocks_in_order():
        role_of[b.start_offset] = ra.get_block_role(b)
    for b in cfg.get_blocks_in_order():
        owners = [type(r).__name__ for r in regions if b in r.blocks]
        print(f'{indent}block {b.start_offset}-{b.end_offset} '
              f'role={role_of[b.start_offset]} regions={owners} '
              f'succ={[s.start_offset for s in b.successors]} '
              f'pred={[s.start_offset for s in b.predecessors]}')
        for i in b.instructions:
            print(f'{indent}    {i.offset:5d} {i.opname} {i.arg}')
    for r in regions:
        print(f'{indent}region {type(r).__name__} entry={r.entry.start_offset if r.entry else None} '
              f'blocks={sorted(x.start_offset for x in r.blocks)}')


def main():
    src = Path(sys.argv[1]).read_text(encoding='utf-8')
    code = compile(src, '<t>', 'exec')
    dump_code(code)
    for c in code.co_consts:
        if hasattr(c, 'co_code'):
            dump_code(c, '  ')


if __name__ == '__main__':
    main()
