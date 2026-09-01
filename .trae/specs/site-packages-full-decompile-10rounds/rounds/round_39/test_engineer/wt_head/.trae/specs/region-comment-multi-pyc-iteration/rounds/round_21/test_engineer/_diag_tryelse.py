"""R21 diag: dump CFG blocks + TRY regions + try-else detection for 2nd `_target` (stream)."""
import marshal
import sys
import types

sys.path.insert(0, r'f:/Downloads/pythoncdc-main')

from core.cfg import build_cfg  # noqa: E402
from core.cfg.region_analyzer import RegionAnalyzer  # noqa: E402


def load_pyc(path):
    with open(path, 'rb') as f:
        f.read(16)
        return marshal.load(f)


def collect(code, out):
    out.append(code)
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            collect(c, out)
    return out


def main():
    root = load_pyc(r'f:/Downloads/pythoncdc-main/site-packages/IQCommon/logger/handlers.pyc')
    targets = [c for c in collect(root, []) if c.co_name == '_target']
    t = targets[-1]  # stream version
    print(f'== _target (stream) varnames={t.co_varnames} ==')
    print(f'exceptiontable entries:')
    try:
        for e in t.co_exceptiontable:
            print(f'  try[{e.start}-{e.end}) handler@{e.target} depth={e.depth} lasti={e.lasti}')
    except Exception as ex:
        print(f'  (no exceptiontable: {ex})')

    cfg = build_cfg(t)
    blocks = list(cfg.blocks.values()) if isinstance(cfg.blocks, dict) else list(cfg.blocks)
    print(f'--- blocks ({len(blocks)}) ---')
    for b in sorted(blocks, key=lambda x: x.start_offset):
        ops = ' '.join(f'{i.offset}:{i.opname}' for i in b.instructions
                       if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'))
        succs = sorted(s.start_offset for s in b.successors)
        print(f'block@{b.start_offset:4d} end={b.end_offset:4d} succs={succs}: {ops}')

    ra = RegionAnalyzer(cfg)
    regions = ra.analyze()
    print(f'\n--- regions ({len(regions)}) ---')
    for r in regions:
        print(f'{type(r).__name__} entry@{getattr(r, "entry", None) and getattr(r.entry, "start_offset", None)}'
              f' blocks={[getattr(b,"start_offset",None) for b in getattr(r, "blocks", [])]}')
        if hasattr(r, 'except_handlers'):
            for (exc, name, hb) in r.except_handlers:
                print(f'  handler exc={exc} name={name} blocks={[b.start_offset for b in hb]}')
            print(f'  try_offset_end={getattr(r, "try_offset_end", None)}')
            print(f'  handler_entry_blocks={[b.start_offset for b in getattr(r, "handler_entry_blocks", [])]}')
            try:
                eb = ra._find_try_else_blocks(r)
                print(f'  _find_try_else_blocks -> {[b.start_offset for b in eb]}')
            except Exception as ex:
                print(f'  _find_try_else_blocks ERROR: {ex}')


if __name__ == '__main__':
    main()
