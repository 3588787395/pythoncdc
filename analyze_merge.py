import sys, marshal, types
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')
from core.cfg import build_cfg
from core.cfg.dominator_analyzer import DominatorAnalyzer

pyc = 'F:/Downloads/pythoncdc-main/site-packages/IQEngine/plugins/plugin_system_matcher/matcher.pyc'
with open(pyc, 'rb') as f:
    f.read(16); orig = marshal.load(f)

def extract(co):
    r = {}; r[co.co_name or '<module>'] = co
    for c in co.co_consts:
        if isinstance(c, types.CodeType): r.update(extract(c))
    return r

om = extract(orig)
match_co = om['match']

cfg = build_cfg(match_co)

# Get blocks for the if condition at offset 816
block_816 = cfg.get_block_by_offset(816)
if block_816:
    # Get conditional successors
    cond_succs = list(block_816.conditional_successors)
    print(f"Block 816 conditional successors:")
    for s in cond_succs:
        print(f"  {s.start_offset}")
    
    # Get the then and else successors
    last_instr = block_816.get_last_instruction()
    print(f"\nLast instr: {last_instr.opname} arg={last_instr.arg} argval={last_instr.argval}")
    
    # The false branch target
    false_target = cfg.get_block_by_offset(last_instr.argval)
    print(f"False target: {false_target.start_offset if false_target else None}")
    
    # Find the true successor (fall-through)
    succs = list(block_816.successors)
    print(f"All successors: {[s.start_offset for s in succs]}")
    
    then_succ = None
    else_succ = None
    for s in succs:
        if s == false_target:
            else_succ = s
        else:
            then_succ = s
    print(f"then_succ={then_succ.start_offset if then_succ else None}, else_succ={else_succ.start_offset if else_succ else None}")
    
    # Find nearest common post-dominator
    if then_succ and else_succ:
        dom_analyzer = DominatorAnalyzer(cfg)
        merge = dom_analyzer.find_nearest_common_post_dominator({then_succ, else_succ})
        print(f"\nNearest common post-dominator of then and else: {merge.start_offset if merge else None}")
        
        # Also try finding it manually - what blocks post-dominate both then_succ(1068) and else_succ(1324)?
        # Block 2464 should be reachable from both paths
        block_2464 = cfg.get_block_by_offset(2464)
        print(f"\nBlock 2464 predecessors: {[p.start_offset for p in block_2464.predecessors]}")
        print(f"Block 2464 successors: {[s.start_offset for s in block_2464.successors]}")
