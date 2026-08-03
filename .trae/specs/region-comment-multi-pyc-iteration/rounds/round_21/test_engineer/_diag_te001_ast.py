"""R21 diag: trace AST generation for te001 to find continue->pass bug."""
import marshal, sys, types
sys.path.insert(0, r'f:/Downloads/pythoncdc-main')
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator

PYC = r'f:/Downloads/pythoncdc-main/.trae/specs/region-comment-multi-pyc-iteration/rounds/round_21/test_engineer/minimal_repros/__pycache__/te001_loop_continue.cpython-311.pyc'

def load_pyc(path):
    with open(path, 'rb') as f:
        f.read(16)
        return marshal.load(f)

def main():
    code = load_pyc(PYC)
    for c in code.co_consts:
        if isinstance(c, types.CodeType) and c.co_name == 'f':
            func_code = c
            break

    cfg = build_cfg(func_code)
    ra = RegionAnalyzer(cfg)
    regions = ra.analyze()

    # Find TryExceptRegion
    for r in regions:
        if type(r).__name__ == 'TryExceptRegion':
            print(f'TryExceptRegion entry@{r.entry.start_offset}')
            print(f'  handler_entry_blocks={[b.start_offset for b in r.handler_entry_blocks]}')
            print(f'  try_blocks={[b.start_offset for b in r.try_blocks]}')
            print(f'  else_blocks={[b.start_offset for b in getattr(r, "else_blocks", [])]}')
            print(f'  has_else={getattr(r, "has_else", None)}')
            for exc, name, hb in r.except_handlers:
                print(f'  handler exc={exc} name={name} blocks={[b.start_offset for b in hb]}')
                for b in hb:
                    ops = [(i.offset, i.opname, i.argval) for i in b.instructions
                           if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                    print(f'    block@{b.start_offset}: {ops}')

    # Try AST generation with detailed logging
    gen = RegionASTGenerator(cfg, ra)
    gen.generate()


if __name__ == '__main__':
    main()
