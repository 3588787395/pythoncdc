"""R22: simulate BFS in _find_loop_else for api_base while-else"""
import marshal, sys, types, json
sys.path.insert(0, r'f:/Downloads/pythoncdc-main')
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion, RegionType, BACKWARD_JUMP_OPS

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

b104 = [b for b in blocks if b.start_offset == 104][0]
b106 = [b for b in blocks if b.start_offset == 106][0]

print(f'block@104 successors: {[s.start_offset for s in b104.successors]}')
print(f'block@106 in b104.successors: {b106 in b104.successors}')
print(f'block@106 predecessors: {[p.start_offset for p in b106.predecessors]}')

# Simulate the BFS manually
body_set = {b for b in blocks if b.start_offset in (10, 64, 66)}
header = [b for b in blocks if b.start_offset == 10][0]
body_set.add(header)

non_return_successors = [b104]

else_blocks = []
visited = set()
stack = list(non_return_successors)
step = 0
while stack:
    cur = stack.pop()
    step += 1
    print(f'\nStep {step}: processing block@{cur.start_offset}')
    if cur in visited or cur in body_set:
        print(f'  SKIP: in_visited={cur in visited} in_body={cur in body_set}')
        continue
    if ra._is_except_handler_block(cur):
        print(f'  SKIP: except_handler')
        continue
    visited.add(cur)
    else_blocks.append(cur)
    print(f'  ADDED to else_blocks')
    if ra._check_block_has_trailing_return_none(cur):
        print(f'  STOP BFS: trailing_return_none')
        continue
    cur_last = cur.get_last_instruction()
    print(f'  last instruction: {cur_last.opname if cur_last else None}')
    if cur_last and cur_last.opname in ('RETURN_VALUE', 'RETURN_CONST', 'RERAISE'):
        print(f'  STOP BFS: RETURN')
        continue
    if cur_last and cur_last.opname in BACKWARD_JUMP_OPS:
        print(f'  STOP BFS: BACKWARD_JUMP')
        continue
    for succ in cur.successors:
        if succ not in visited and succ not in body_set:
            stack.append(succ)
            print(f'  PUSH succ@{succ.start_offset}')

print(f'\nFinal else_blocks: {[b.start_offset for b in else_blocks]}')
