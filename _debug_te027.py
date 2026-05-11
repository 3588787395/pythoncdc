import sys
sys.path.insert(0, '.')

source_code = 'try:\n    while x < 3:\n        x += 1\nexcept:\n    y = 1'

original_code = compile(source_code, '<test>', 'exec')

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer

cfg_builder = CFGBuilder()
cfg = cfg_builder.build(original_code)

# Block 60 的详细信息
block60 = cfg.get_block_by_offset(60)
print('Block 60:')
print('  predecessors: %s' % ([b.start_offset for b in block60.predecessors]))

# Block 46 的详细信息
block46 = cfg.get_block_by_offset(46)
print('Block 46:')
print('  instructions: %s' % ([i.opname for i in block46.instructions]))
print('  predecessors: %s' % ([b.start_offset for b in block46.predecessors]))

# 手动模拟 _classify_handler_with_cleanup
print()
print('Manual simulation of _classify_handler_with_cleanup for block 60:')
target_offset = 60
visited = {target_offset}
worklist = list(block60.predecessors)  # [46]
print('  Initial worklist: %s' % ([b.start_offset for b in worklist]))

while worklist:
    pred = worklist.pop()
    if pred.start_offset in visited:
        continue
    visited.add(pred.start_offset)
    
    has_push_exc = any(i.opname == 'PUSH_EXC_INFO' for i in pred.instructions)
    has_check = any(i.opname == 'CHECK_EXC_MATCH' for i in pred.instructions)
    has_check_eg = any(i.opname == 'CHECK_EG_MATCH' for i in pred.instructions)
    has_reraise = any(i.opname == 'RERAISE' for i in pred.instructions)
    has_copy = any(i.opname == 'COPY' for i in pred.instructions)
    has_pop_except = any(i.opname == 'POP_EXCEPT' for i in pred.instructions)
    
    print('  Checking pred block %d:' % pred.start_offset)
    print('    has_push_exc=%s, has_check=%s, has_reraise=%s' % (has_push_exc, has_check, has_reraise))
    print('    has_copy=%s, has_pop_except=%s' % (has_copy, has_pop_except))
    
    if has_push_exc and has_check:
        result = "'except'"
        print("    -> return %s" % result)
        break
    if has_push_exc and has_check_eg:
        result = "'except_star'"
        print("    -> return %s" % result)
        break
    if has_push_exc and not has_check and not has_check_eg and not has_reraise:
        result = "'except'"
        print("    -> return %s" % result)
        break
    
    has_copy_pop = has_copy and has_pop_except
    print('    has_copy_pop=%s' % has_copy_pop)
    if not has_copy_pop:
        worklist.extend(pred.predecessors)
        print('    -> extending worklist')

# 检查第二个条目为什么被过滤
print()
print('Checking why entry 2 (target=60) is filtered:')
for entry in cfg.exception_table:
    entry_target = entry['target']
    handler_block = cfg.get_block_by_offset(entry_target)
    
    # 测试 is_cleanup_only
    is_cleanup_only = (
        handler_block.instructions[0].opname not in ('PUSH_EXC_INFO', 'WITH_EXCEPT_START')
        and any(i.opname == 'COPY' for i in handler_block.instructions)
        and any(i.opname == 'POP_EXCEPT' for i in handler_block.instructions)
        and any(i.opname == 'RERAISE' for i in handler_block.instructions)
    )
    print('Entry target=%d: is_cleanup_only=%s' % (entry_target, is_cleanup_only))
    
    if is_cleanup_only:
        handler_type = 'except'  # 假设被分类为 except
        actual_handler_start = 46  # 假设 actual 是 46
        
        if actual_handler_start != entry_target:
            print('  actual != target, checking conditions...')
            actual_handler_block = cfg.get_block_by_offset(actual_handler_start)
            has_push_exc = any(i.opname == 'PUSH_EXC_INFO' for i in actual_handler_block.instructions)
            has_reraise = any(i.opname == 'RERAISE' for i in actual_handler_block.instructions)
            has_check = any(i.opname in ('CHECK_EXC_MATCH', 'CHECK_EG_MATCH') for i in actual_handler_block.instructions)
            print('    actual: has_push_exc=%s, has_reraise=%s, has_check=%s' % (has_push_exc, has_reraise, has_check))
            if has_push_exc and has_reraise and not has_check:
                print('    -> pass (keep entry)')
            elif has_push_exc and has_check:
                print('    -> continue (skip entry)')
            elif handler_type != 'finally':
                print('    -> continue (skip entry)')
        elif handler_type != 'finally':
            print('  actual == target, handler_type=%s != finally' % handler_type)
            print('    -> continue (skip entry)')
