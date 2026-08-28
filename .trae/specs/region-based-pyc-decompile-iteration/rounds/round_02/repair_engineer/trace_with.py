#!/usr/bin/env python3
"""追踪 _generate_with 标记 generated 的块，以及 generate() 最终 AST 的语句序列。"""
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

orig_with = rag.RegionASTGenerator._generate_with


def traced_with(self, region):
    print(f'>>> _generate_with entry={region.entry.start_offset} '
          f'blocks={sorted(b.start_offset for b in region.blocks)}')
    r = orig_with(self, region)
    print(f'<<< _generate_with -> {r}')
    return r


rag.RegionASTGenerator._generate_with = traced_with

orig_gbs = rag.RegionASTGenerator._generate_block_statements


def traced_gbs(self, block, _cjb_parent=None):
    if block.start_offset in (0, 86, 132):
        print(f'>>> _generate_block_statements block={block.start_offset} '
              f'generated={block in self.generated_blocks}')
        for fr in traceback.extract_stack()[-5:-1]:
            print(f'      @ {fr.filename.split("core")[-1]}:{fr.lineno} {fr.name}')
    r = orig_gbs(self, block, _cjb_parent)
    if block.start_offset in (0, 86, 132):
        print(f'<<< _generate_block_statements block={block.start_offset} -> {r}')
    return r


rag.RegionASTGenerator._generate_block_statements = traced_gbs

orig_bfd = rag.RegionASTGenerator._build_function_def


def traced_bfd(self, *a, **kw):
    r = orig_bfd(self, *a, **kw)
    if r and isinstance(r, dict) and r.get('type') == 'FunctionDef':
        body = r.get('body') or []
        print(f'### FunctionDef {r.get("name")} body types = '
              f'{[s.get("type") for s in body if isinstance(s, dict)]}')
    return r


rag.RegionASTGenerator._build_function_def = traced_bfd

src = Path(sys.argv[1]).read_text(encoding='utf-8')
print(decompile(src, str(sys.argv[1])))
