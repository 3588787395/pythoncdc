"""R22: trace natural_exit and BFS path for api_base while-else"""
import marshal, sys, types, json
sys.path.insert(0, r'f:/Downloads/pythoncdc-main')
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion
from core.cfg.dominator_analyzer import DominatorAnalyzer

with open(r'f:/Downloads/pythoncdc-main/pyc_index.json', 'r') as f:
    index = json.load(f)

pyc_path = None
for e in index:
    if 'api_base.pyc' in e.get('path', ''):
        pyc_path = e['path']
        break

with open(pyc_path, 'rb') as f:
    f.read(16)
    root = marshal.load(f)

def collect(code, out):
    out.append(code)
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            collect(c, out)
    return out

for c in collect(root, []):
    if c.co_name == 'decorate_api_exc':
        code = c
        break

cfg = build_cfg(code)
ra = RegionAnalyzer(cfg)

blocks = sorted(
    (list(cfg.blocks.values()) if isinstance(cfg.blocks, dict) else list(cfg.blocks)),
    key=lambda x: x.start_offset
)
header = [b for b in blocks if b.start_offset == 10][0]
condition_block = [b for b in blocks if b.start_offset == 0][0]

body_set = {b for b in blocks if b.start_offset in (10, 64, 66)}

# loop_successors (from body blocks)
loop_successors = []
for b in body_set:
    for s in b.successors:
        if s not in body_set and s != header and s not in loop_successors:
            loop_successors.append(s)

# Plus cond_exit from condition_block
cond_last = condition_block.get_last_instruction()
if cond_last and cond_last.opname == 'POP_JUMP_FORWARD_IF_FALSE':
    cond_exit = cfg.get_block_by_offset(cond_last.argval)
    if cond_exit and cond_exit not in body_set and cond_exit not in loop_successors:
        loop_successors.append(cond_exit)

print(f'loop_successors = {[b.start_offset for b in loop_successors]}')

# Compute natural_exit
natural_exit = ra.dom_analyzer.find_nearest_common_post_dominator(set(loop_successors))
print(f'natural_exit = {natural_exit.start_offset if natural_exit else None}')
print(f'natural_exit in body_set = {natural_exit in body_set if natural_exit else "N/A"}')

# Check _is_early_return_block for each loop_successor
for s in loop_successors:
    print(f'  block@{s.start_offset}: _is_early_return={ra._is_early_return_block(s)} _has_trailing_return_none={ra._check_block_has_trailing_return_none(s)}')

# The filtered non_return_successors
non_return_successors = [s for s in loop_successors
                        if not ra._check_block_has_trailing_return_none(s)]
non_return_successors = [s for s in non_return_successors
                        if not ra._is_early_return_block(s)
                        and not ra._is_except_handler_block(s)]
print(f'\nnon_return_successors = {[b.start_offset for b in non_return_successors]}')
