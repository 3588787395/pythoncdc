"""Dump region tree for a function in a pyc: regions, blocks, AST output.
Usage: python _r2_dbg_region.py <pyc> <funcname>
"""
import sys, marshal, types, dis
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')

def find_code(co, name, result=None):
    if result is None: result = []
    if co.co_name == name: result.append(co)
    for c in co.co_consts:
        if isinstance(c, types.CodeType): find_code(c, name, result)
    return result

def dump_region(r, indent=0, seen=None):
    pad = '  ' * indent
    seen = seen if seen is not None else set()
    if id(r) in seen:
        print(f"{pad}<recursive {type(r).__name__}>")
        return
    seen.add(id(r))
    blocks = getattr(r, 'blocks', None)
    offs = []
    if blocks:
        try:
            offs = sorted(b.start_offset for b in blocks)
        except Exception:
            offs = ['?']
    extra = ''
    cb = getattr(r, 'condition_block', None)
    if cb is not None: extra += f' cond={getattr(cb, "start_offset", "?")}'
    en = getattr(r, 'entry', None)
    if en is not None and not isinstance(en, (int, str)): extra += f' entry={getattr(en, "start_offset", "?")}'
    mb = getattr(r, 'merge_block', None)
    if mb is not None and not isinstance(mb, (int, str)): extra += f' merge={getattr(mb, "start_offset", "?")}'
    rt = getattr(r, 'region_type', None)
    if rt is not None: extra += f' rtype={getattr(rt, "name", rt)}'
    print(f"{pad}{type(r).__name__}{extra} blocks={offs[:20]}{'...' if len(offs) > 20 else ''}")
    for attr in ('body_regions', 'then_regions', 'child_regions', 'sub_regions', 'nested_regions', 'orelse_regions', 'handlers'):
        sub = getattr(r, attr, None)
        if sub:
            print(f"{pad}  {attr}:")
            for s in sub:
                dump_region(s, indent + 2, seen)

def main():
    pyc, fname = sys.argv[1], sys.argv[2]
    with open(pyc, 'rb') as f:
        f.read(16)
        top = marshal.load(f)
    codes = find_code(top, fname)
    if not codes:
        print(f'function {fname} not found'); return 1
    co = codes[0]
    from core.cfg.cfg_builder import CFGBuilder
    builder = CFGBuilder()
    cfg = builder.build(co)
    print(f'=== CFG for {fname}: {len(cfg.blocks)} blocks ===')
    from core.cfg.region_analyzer import RegionAnalyzer
    ra = RegionAnalyzer(cfg)
    regions = ra.analyze()
    print(f'=== {len(regions)} top-level regions ===')
    for r in regions:
        dump_region(r, 0)
    gen = None
    from core.cfg.region_ast_generator import RegionASTGenerator
    gen = RegionASTGenerator(cfg)
    ast_out = gen.generate()
    import json
    print('=== AST ===')
    def show(n, d=0):
        if isinstance(n, dict):
            t = n.get('type')
            keys = [k for k in n.keys() if k not in ('type',)]
            desc = ''
            if t == 'Expr' and isinstance(n.get('value'), dict):
                desc = ' value=' + str(n['value'].get('type'))
            print('  ' * d + f'{t}{desc}')
            for k in ('body', 'orelse', 'finalbody'):
                v = n.get(k)
                if isinstance(v, list):
                    print('  ' * (d + 1) + k + ':')
                    for c in v: show(c, d + 2)
            if t == 'If' and isinstance(n.get('test'), dict):
                print('  ' * (d + 1) + 'test: ' + str(n['test'])[:120])
            if t == 'Return':
                print('  ' * (d + 1) + 'value: ' + str(n.get('value'))[:120])
        elif isinstance(n, list):
            for c in n: show(c, d)
    show(ast_out)

if __name__ == '__main__':
    main()
