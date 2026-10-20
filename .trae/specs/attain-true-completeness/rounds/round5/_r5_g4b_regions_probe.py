# -*- coding: utf-8 -*-
"""R5 synth g4b triage: dump blocks/regions/generated for multiple units."""
import marshal
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from core.cfg.cfg_builder import CFGBuilder  # noqa: E402
from core.cfg.region_ast_generator import RegionASTGenerator  # noqa: E402

UNITS = sys.argv[1:] or ['g4b_wt_with_continue', 'g4b_wt_nested_with']

with open(r'test_repros\round5\rec1_synth_g4b_b70_whiletrue_with.pyc', 'rb') as f:
    code = marshal.loads(f.read()[16:])

lines = []
for name in UNITS:
    target = next(c for c in code.co_consts
                  if hasattr(c, 'co_name') and c.co_name == name)
    builder = CFGBuilder()
    cfg = builder.build(target)
    gen = RegionASTGenerator(cfg)
    res = gen.generate()
    analyzer = gen.region_analyzer
    lines.append('########## %s' % name)
    lines.append('=== blocks ===')
    for b in sorted(cfg.blocks.values(), key=lambda x: x.start_offset):
        lines.append('BLK@%s..%s succ=%s pred=%s role=%s' % (
            b.start_offset,
            b.instructions[-1].offset if b.instructions else None,
            [s.start_offset for s in b.successors],
            [p.start_offset for p in b.predecessors],
            analyzer.get_block_role(b)))
        lines.append('    ' + ' | '.join(
            '%s@%s%s' % (i.opname, i.offset,
                         '->%s' % i.argval if i.opname.startswith(
                             ('JUMP', 'POP_JUMP', 'FOR_ITER')) else '')
            for i in b.instructions))
    lines.append('=== regions ===')
    for r in gen.regions:
        lines.append('REGION %s entry@%s blocks=%s' % (
            type(r).__name__, r.entry.start_offset,
            [b.start_offset for b in getattr(r, 'blocks', [])]))
        for attr in ('condition_block', 'header_block', 'then_blocks', 'else_blocks',
                     'with_blocks', 'cleanup_blocks', 'exception_blocks',
                     'body_blocks', 'break_blocks', 'exit_block'):
            v = getattr(r, attr, None)
            if v is None:
                continue
            if isinstance(v, (list, set)):
                lines.append('    %s=%s' % (attr, [x.start_offset for x in v]))
            else:
                lines.append('    %s=@%s' % (attr, v.start_offset))

    def dump(node, depth=0):
        pad = '  ' * depth
        if isinstance(node, dict):
            t = node.get('type')
            extra = ''
            for k in ('value', 'targets', 'items', 'op', 'func'):
                v = node.get(k)
                if v is not None and not isinstance(v, (dict, list)):
                    extra += ' %s=%r' % (k, v)
            lines.append('%s%s%s' % (pad, t, extra))
            for k in ('body', 'orelse', 'finalbody', 'handlers', 'items', 'cases'):
                v = node.get(k)
                if isinstance(v, list):
                    lines.append('%s %s:[' % (pad, k))
                    for c in v:
                        dump(c, depth + 2)
                    lines.append('%s ]' % pad)
                elif isinstance(v, dict):
                    lines.append('%s %s:[' % (pad, k))
                    dump(v, depth + 2)
                    lines.append('%s ]' % pad)
            for k in ('test',):
                v = node.get(k)
                if isinstance(v, dict):
                    lines.append('%s test:[' % pad)
                    dump(v, depth + 2)
                    lines.append('%s ]' % pad)
        elif isinstance(node, list):
            lines.append('%s[' % pad)
            for c in node:
                dump(c, depth + 1)
            lines.append('%s]' % pad)
        else:
            lines.append('%s%r' % (pad, node))

    lines.append('=== generated dict ===')
    dump(res)

out = '\n'.join(lines)
open(os.path.join(HERE, '_r5_g4b_regions.txt'), 'w', encoding='utf-8').write(out)
print('written', len(lines), 'lines')
