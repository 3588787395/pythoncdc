"""Trace _generate_try and _generate_loop for create_full_graph to find T3 root cause."""
import os, sys, marshal
sys.path.insert(0, r'F:/Downloads/pythoncdc-main')

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, TryExceptRegion, LoopRegion, IfRegion, BlockRole
from core.cfg.region_ast_generator import RegionASTGenerator

PYC = r'F:/Downloads/pythoncdc-main/site-packages/IQCommon/graph.pyc'
with open(PYC, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

target = None
for c in code.co_consts:
    if hasattr(c, 'co_code') and c.co_name == 'ModelGraph':
        for cc in c.co_consts:
            if hasattr(cc, 'co_code') and cc.co_name == 'create_full_graph':
                target = cc
                break
    if target: break

cfg_builder = CFGBuilder()
cfg = cfg_builder.build(target)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

print('=== Regions summary ===')
for r in analyzer.regions:
    ptype = type(r.parent).__name__ if r.parent else 'None'
    print(f'  [{type(r).__name__}] entry={r.entry.start_offset} parent={ptype}')

# Check parent of OUTER try (entry=14)
outer = None
inner = None
loop = None
for r in analyzer.regions:
    if isinstance(r, TryExceptRegion) and r.entry.start_offset == 14:
        outer = r
    elif isinstance(r, TryExceptRegion) and r.entry.start_offset == 318:
        inner = r
    elif isinstance(r, LoopRegion) and r.entry.start_offset == 42:
        loop = r

print(f'\nOUTER try: entry={outer.entry.start_offset} parent={type(outer.parent).__name__}')
print(f'  parent.entry={outer.parent.entry.start_offset if outer.parent else None}')
print(f'  parent is loop? {outer.parent is loop}')
print(f'  parent is None? {outer.parent is None}')
print(f'  try_blocks={[b.start_offset for b in outer.try_blocks]}')
print(f'  handler_entry_blocks={[b.start_offset for b in outer.handler_entry_blocks]}')
print(f'  blocks={[b.start_offset for b in sorted(outer.blocks, key=lambda b: b.start_offset)]}')
print(f'  block_to_region[640] is outer? {analyzer.block_to_region.get(outer.handler_entry_blocks[0]) is outer}')

print(f'\nINNER try: entry={inner.entry.start_offset} parent={type(inner.parent).__name__}')
print(f'  parent.entry={inner.parent.entry.start_offset if inner.parent else None}')
print(f'  parent is outer? {inner.parent is outer}')
print(f'  parent is loop? {inner.parent is loop}')

print(f'\nLoop: entry={loop.entry.start_offset} parent={type(loop.parent).__name__}')
print(f'  parent.entry={loop.parent.entry.start_offset if loop.parent else None}')
print(f'  blocks count={len(loop.blocks)}')
print(f'  body_blocks={[b.start_offset for b in loop.body_blocks]}')
print(f'  else_blocks={[b.start_offset for b in loop.else_blocks]}')

# Check block_to_region for OUTER's handler_entry (640) and handler body (658, 758)
print('\n=== block_to_region for OUTER handler blocks ===')
_all_cfg_blocks = list(cfg.blocks.values()) if isinstance(cfg.blocks, dict) else list(cfg.blocks)
for off in [640, 658, 758, 762, 764]:
    blk = None
    for b in _all_cfg_blocks:
        if getattr(b, 'start_offset', None) == off:
            blk = b
            break
    if blk:
        owner = analyzer.block_to_region.get(blk)
        print(f'  block@{off}: owner={type(owner).__name__} entry={owner.entry.start_offset if owner and owner.entry else None}')

# Check if OUTER.entry (block 14) is in LoopRegion.blocks
print(f'\nOUTER.entry (14) in LoopRegion.blocks? {outer.entry in loop.blocks}')
print(f'OUTER.entry (14) in LoopRegion.body_blocks? {outer.entry in loop.body_blocks}')
print(f'OUTER.entry (14) block_to_region owner: ', end='')
owner14 = analyzer.block_to_region.get(outer.entry)
print(f'{type(owner14).__name__} entry={owner14.entry.start_offset if owner14 and owner14.entry else None}')

# Now let's instrument and run the generation
print('\n=== Running generation with trace ===')
gen = RegionASTGenerator(cfg, analyzer)

# Monkey-patch _generate_try to trace
orig_generate_try = gen._generate_try
def traced_generate_try(region):
    print(f'\n[TRACE _generate_try] ENTER region.entry={region.entry.start_offset} parent={type(region.parent).__name__ if region.parent else None}')
    print(f'  try_blocks={[b.start_offset for b in region.try_blocks]}')
    print(f'  handler_entry_blocks={[b.start_offset for b in region.handler_entry_blocks]}')
    print(f'  generated_blocks BEFORE: {sorted(b.start_offset for b in gen.generated_blocks)}')
    result = orig_generate_try(region)
    print(f'[TRACE _generate_try] EXIT region.entry={region.entry.start_offset}')
    print(f'  generated_blocks AFTER: {sorted(b.start_offset for b in gen.generated_blocks)}')
    if result:
        # Print the AST structure briefly
        import json
        def _simplify(node):
            if isinstance(node, dict):
                t = node.get('type', node.get('kind', '?'))
                if t == 'Try':
                    return {'type': 'Try', 'handlers': len(node.get('handlers', [])), 'body_len': len(node.get('body', []))}
                if t in ('ExceptHandler',):
                    return {'type': 'ExceptHandler', 'type_': str(node.get('type', '?'))[:30]}
                return {k: _simplify(v) for k, v in node.items() if k in ('type', 'body', 'handlers', 'orelse', 'finalbody', 'test')}
            if isinstance(node, list):
                return [_simplify(n) for n in node[:5]]
            return str(node)[:50]
        try:
            print(f'  result: {json.dumps(_simplify(result), default=str)[:500]}')
        except Exception as e:
            print(f'  result: (serialize error {e})')
    return result
gen._generate_try = traced_generate_try

orig_generate_loop = gen._generate_loop
def traced_generate_loop(region, **kw):
    print(f'\n[TRACE _generate_loop] ENTER region.entry={region.entry.start_offset} parent={type(region.parent).__name__ if region.parent else None}')
    print(f'  body_blocks={[b.start_offset for b in region.body_blocks]}')
    print(f'  else_blocks={[b.start_offset for b in region.else_blocks]}')
    print(f'  children={[type(c).__name__+":"+str(c.entry.start_offset) for c in region.children]}')
    result = orig_generate_loop(region, **kw)
    print(f'[TRACE _generate_loop] EXIT region.entry={region.entry.start_offset}')
    return result
gen._generate_loop = traced_generate_loop

try:
    result = gen.generate()
    print('\n=== Generation result (top-level) ===')
    if result:
        import json
        def _simplify(node, depth=0):
            if depth > 8: return '...'
            if isinstance(node, dict):
                t = node.get('type', '?')
                if t in ('FunctionDef', 'ClassDef'):
                    return {'type': t, 'name': node.get('name'), 'body': [_simplify(b, depth+1) for b in node.get('body', [])[:10]]}
                if t == 'Try':
                    return {'type': 'Try', 'body': [_simplify(b, depth+1) for b in node.get('body', [])[:5]], 'handlers': [_simplify(h, depth+1) for h in node.get('handlers', [])], 'orelse': [_simplify(b, depth+1) for b in node.get('orelse', [])[:3]]}
                if t == 'ExceptHandler':
                    return {'type': 'ExceptHandler', 'exc': str(node.get('type', '?'))[:30], 'body': [_simplify(b, depth+1) for b in node.get('body', [])[:5]]}
                if t in ('For', 'While'):
                    return {'type': t, 'body': [_simplify(b, depth+1) for b in node.get('body', [])[:8]], 'orelse': [_simplify(b, depth+1) for b in node.get('orelse', [])[:3]]}
                if t == 'If':
                    return {'type': 'If', 'body': [_simplify(b, depth+1) for b in node.get('body', [])[:5]], 'orelse': [_simplify(b, depth+1) for b in node.get('orelse', [])[:5]]}
                return {'type': t}
            if isinstance(node, list):
                return [_simplify(n, depth+1) for n in node[:10]]
            return str(node)[:30]
        print(json.dumps(_simplify(result), default=str, indent=2)[:3000])
except Exception as e:
    import traceback
    print(f'Generation error: {e}')
    traceback.print_exc()
