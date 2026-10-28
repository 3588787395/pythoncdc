# Dump CFG block structure of enum._find_new_ to locate the use_args mis-nesting.
import sys, types, dis, textwrap
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')
from core.cfg.cfg_builder import build_cfg

# Extract original _find_new_ source (lines 1007-1049 of D:/Python/Lib/enum.py)
lines = open(r'D:\Python\Lib\enum.py', encoding='utf-8').read().split('\n')
start = next(i for i,l in enumerate(lines) if 'def _find_new_' in l)
# find the end: next line at same/less indent that starts a def/class at col 4 or is 'EnumMeta'
end = start+1
while end < len(lines):
    l = lines[end]
    if l.startswith('    def ') or l.startswith('class ') or l.startswith('EnumMeta'):
        break
    end += 1
raw = '\n'.join(lines[start:end])
src = textwrap.dedent(raw)
print('=== SRC lines', start+1, 'to', end, '===')

code = compile(src + '\n', '<fnc>', 'exec')
# the function code object is the first const
fnc = [c for c in code.co_consts if isinstance(c, types.CodeType)][0]
print('func co_name', fnc.co_name, 'nlocals', fnc.co_nlocals)

cfg = build_cfg(fnc, name='_find_new_')
print('=== BLOCKS ===')
for b in cfg.blocks.values():
    succs = sorted(x.id for x in (getattr(b, 'successors', set()) or set()))
    preds = sorted(x.id for x in (getattr(b, 'predecessors', set()) or set()))
    # first/last line
    lns = [getattr(i, 'starts_line', None) for i in b.instructions] if hasattr(b,'instructions') else []
    lns = [x for x in lns if x]
    span = f'{min(lns)}-{max(lns)}' if lns else '?'
    # show target of conditional jumps
    print(f'B{b.id} lines[{span}] preds={preds} succs={succs} ninst={len(getattr(b,"instructions",[]))}')
    for i in getattr(b, 'instructions', []):
        op = getattr(i, 'opname', '?')
        arg = getattr(i, 'argrepr', '')
        print(f'    {op} {arg}')
