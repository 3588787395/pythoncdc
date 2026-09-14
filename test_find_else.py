import sys
sys.path.insert(0, '.')
from core.cfg import build_cfg
from core.cfg.dominator_analyzer import DominatorAnalyzer, LoopAnalyzer
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion, RegionType

src = '''
def test_while_else_nested_break(data):
    while data:
        item = data[0]
        if item < 0:
            data.pop(0)
            continue
        if item == 0:
            break
        data.pop(0)
    else:
        data.append(-1)
    return data
'''

code = compile(src, '<test>', 'exec')
for c in code.co_consts:
    if hasattr(c, 'co_code'):
        cfg = build_cfg(c)
        ra = RegionAnalyzer(cfg)
        
        # Manually simulate _find_loop_else for inner loop (header=6)
        h6 = cfg.get_block_by_offset(6)
        body_6 = {h6, cfg.get_block_by_offset(34), cfg.get_block_by_offset(78), 
                  cfg.get_block_by_offset(90), cfg.get_block_by_offset(92)}
        body_set = body_6
        
        condition_block = cfg.get_block_by_offset(2)
        
        # Compute loop_successors
        header_succs = [s for s in h6.successors if s not in body_set and s != h6]
        print(f'header successors not in body: {[s.start_offset for s in header_succs]}')
        
        # From condition_block (not in body_set)
        cond_exit_targets = []
        if condition_block and condition_block != h6 and condition_block not in body_set:
            cond_last = condition_block.get_last_instruction()
            if cond_last and cond_last.opname == 'POP_JUMP_FORWARD_IF_FALSE' and cond_last.argval is not None:
                cond_exit = cfg.get_block_by_offset(cond_last.argval)
                print(f'condition_block exit target: {cond_exit.start_offset}')
                if cond_exit and cond_exit not in body_set and cond_exit != h6:
                    if cond_exit not in header_succs:
                        header_succs.append(cond_exit)
                    cond_exit_targets.append(cond_exit)
        
        print(f'loop_successors: {[s.start_offset for s in header_succs]}')
        
        # Check body successors
        for block in body_set:
            if block == h6:
                continue
            for succ in block.successors:
                if succ not in body_set and succ != h6 and succ not in header_succs:
                    if condition_block and succ == condition_block:
                        continue
                    print(f'body block {block.start_offset} successor {succ.start_offset} not in body')
                    header_succs.append(succ)
        
        print(f'all loop_successors: {[s.start_offset for s in header_succs]}')
