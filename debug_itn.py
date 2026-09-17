import sys
sys.path.insert(0, '.')
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer
import marshal, types

with open('site-packages/fly/oauthenticator/itn.pyc', 'rb') as f:
    f.read(16)
    code = marshal.load(f)

for const in code.co_consts:
    if isinstance(const, types.CodeType) and const.co_name == 'ITNOAuthenticator':
        for c2 in const.co_consts:
            if isinstance(c2, types.CodeType) and c2.co_name == 'authenticate':
                cfg = build_cfg(c2)
                ra = RegionAnalyzer(cfg, c2)
                ra.analyze()
                for rid, region in enumerate(ra.regions):
                    rtype = type(region).__name__
                    if rtype == 'BoolOpRegion':
                        entry = region.entry
                        merge = region.merge_block
                        blocks = region.blocks
                        op_chain = region.op_chain
                        value_target = getattr(region, 'value_target', None)
                        print("BoolOpRegion %d:" % rid)
                        print("  entry: B%s (@%s)" % (entry.id, entry.start_offset))
                        print("  merge: B%s (@%s)" % (merge.id, merge.start_offset))
                        print("  blocks: %s" % [b.id for b in blocks])
                        print("  op_chain: %s" % [(b.id, op) for b, op in op_chain])
                        print("  value_target: %s" % value_target)
                        # Check if merge block has trailing conditional jump
                        merge_last = merge.get_last_instruction()
                        print("  merge_last: %s" % (merge_last.opname if merge_last else None))
                        if merge_last and merge_last.opname in ('POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_FORWARD_IF_NOT_NONE'):
                            print("  *** merge block has trailing conditional jump! ***")
                break
