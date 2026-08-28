#!/usr/bin/env python3
"""追踪 _generate_assert / _generate_region 的调用来源与区域识别结果。

用法: D:/Python/python.exe trace_assert.py <src_file>
"""
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _find_root(start: Path) -> Path:
    for p in [start] + list(start.parents):
        if (p / 'core' / 'cfg').is_dir() and (p / 'pycdc.py').is_file():
            return p
    raise RuntimeError(start)


ROOT = _find_root(HERE)
sys.path.insert(0, str(ROOT))

from core.cfg import decompile  # noqa: E402
from core.cfg import region_ast_generator as rag  # noqa: E402
from core.cfg import region_analyzer as ra  # noqa: E402

orig_assert = rag.RegionASTGenerator._generate_assert


def traced_assert(self, region, skip_store_targets=None):
    print(f'>>> _generate_assert entry={region.entry.start_offset} '
          f'cond={region.condition_block.start_offset} '
          f'blocks={sorted(b.start_offset for b in region.blocks)}')
    print('    cond_block instrs:')
    for i in region.condition_block.instructions:
        print(f'      {i.offset:5d} {i.opname} {getattr(i, "argrepr", i.arg)}')
    for fr in traceback.extract_stack()[-6:-1]:
        print(f'      @ {fr.filename.split("core")[ -1]}:{fr.lineno} {fr.name}')
    r = orig_assert(self, region, skip_store_targets)
    print(f'<<< _generate_assert -> {r}')
    return r


rag.RegionASTGenerator._generate_assert = traced_assert

orig_analyze = ra.RegionAnalyzer.analyze


def traced_analyze(self):
    rs = orig_analyze(self)
    print('=== REGIONS ===')
    for r in self.regions:
        print(f'  {type(r).__name__} entry={r.entry.start_offset if r.entry else None} '
              f'blocks={sorted(b.start_offset for b in r.blocks)}')
    print('=== BLOCKS ===')
    for b in self.cfg.get_blocks_in_order():
        print(f'  block {b.start_offset}-{b.end_offset} succ={[s.start_offset for s in b.successors]}')
        for i in b.instructions:
            print(f'      {i.offset:5d} {i.opname} {getattr(i, "argrepr", i.arg)}')
    return rs


ra.RegionAnalyzer.analyze = traced_analyze

src = Path(sys.argv[1]).read_text(encoding='utf-8')
print(decompile(src, str(sys.argv[1])))
