#!/usr/bin/env python3
"""R93 analyze: which then_blocks are post-merge and NOT reachable from pre-merge blocks"""
import sys, marshal, types
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion

target_pyc = "site-packages/IQCommon/api/klinedata.pyc"
with open(target_pyc, 'rb') as f:
    f.read(16)
    orig_code = marshal.loads(f.read())

def find_function(code, name):
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                return const
            inner = find_function(const, name)
            if inner:
                return inner
    return None

func_code = find_function(orig_code, 'get_multiminute_his_data')
builder = CFGBuilder()
cfg = builder.build(func_code)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

for r in regions:
    if isinstance(r, IfRegion) and r.entry and r.entry.start_offset == 0:
        mb = r.merge_block  # offset 2710
        then_blocks = r.then_blocks or []
        
        pre_merge = [b for b in then_blocks if b.start_offset < mb.start_offset]
        post_merge = [b for b in then_blocks if b.start_offset >= mb.start_offset]
        
        print(f"IfRegion@0 merge={mb.start_offset}")
        print(f"  pre_merge: {len(pre_merge)} blocks: {[b.start_offset for b in pre_merge]}")
        print(f"  post_merge: {len(post_merge)} blocks: {[b.start_offset for b in post_merge]}")
        
        # BFS from pre_merge blocks to find reachable blocks
        then_set = set(then_blocks)
        reachable = set()
        worklist = list(pre_merge)
        while worklist:
            b = worklist.pop()
            for s in b.successors:
                if s in then_set and s not in reachable:
                    reachable.add(s)
                    worklist.append(s)
        
        print(f"  reachable from pre_merge: {len(reachable)} blocks: {sorted([b.start_offset for b in reachable])}")
        
        # Post-merge blocks NOT reachable from pre-merge
        not_reachable = [b for b in post_merge if b not in reachable]
        print(f"  post_merge NOT reachable: {len(not_reachable)} blocks: {sorted([b.start_offset for b in not_reachable])}")
        
        # Check: is the not_reachable block 2758 the function's implicit return?
        for b in not_reachable:
            print(f"\n  Block {b.start_offset} instructions:")
            for instr in b.instructions:
                print(f"    {instr.offset:4d} {instr.opname:30s} {getattr(instr, 'argval', getattr(instr, 'arg', ''))}")
            print(f"    predecessors: {[p.start_offset for p in b.predecessors]}")
            print(f"    successors: {[s.start_offset for s in b.successors]}")
        break
