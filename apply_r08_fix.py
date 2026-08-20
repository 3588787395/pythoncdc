"""
Round 8 Fix: Prevent blocks with user code (print/call) from being marked as BREAK.

Problem: In validate_data, blocks like Block@194 and Block@366 contain print() calls
followed by return False (in successor blocks). These blocks are incorrectly marked
as BREAK by _detect_break_continue because they're not in body_set and don't contain
RETURN_VALUE themselves.

Fix: In _detect_break_continue, before adding a block to break_blocks_set in the
else branch (line 4765-4780), check if the block contains meaningful user code
(CALL, STORE, etc.). If it does, skip it - it's not a pure break target.
"""
import re

filepath = 'core/cfg/region_analyzer.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the exact code block to patch
old_code = """                        else:
                            if is_back_edge_condition:
                                continue
                            # Fix: 如果后继块是跳回循环头部或循环条件的 JUMP_BACKWARD 块
                            # （即 continue 语句），不应将其归类为 break 块。
                            # 这种情况发生在 try body 内的 continue 块未被纳入
                            # loop_body 但仍属于循环结构时。
                            # while 循环中 continue 跳转到循环条件块（header 的前驱），
                            # for 循环中 continue 跳转到 header 本身。
                            _s_last = s.get_last_instruction()
                            if _s_last and _s_last.opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT'):
                                _s_target = self.cfg.get_block_by_offset(_s_last.argval) if _s_last.argval is not None else None
                                if _s_target == header or _s_target in header.predecessors:
                                    continue_map[s] = 'CONTINUE'
                                    continue
                            break_blocks_set.add(s)"""

new_code = """                        else:
                            if is_back_edge_condition:
                                continue
                            # Fix: 如果后继块是跳回循环头部或循环条件的 JUMP_BACKWARD 块
                            # （即 continue 语句），不应将其归类为 break 块。
                            # 这种情况发生在 try body 内的 continue 块未被纳入
                            # loop_body 但仍属于循环结构时。
                            # while 循环中 continue 跳转到循环条件块（header 的前驱），
                            # for 循环中 continue 跳转到 header 本身。
                            _s_last = s.get_last_instruction()
                            if _s_last and _s_last.opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT'):
                                _s_target = self.cfg.get_block_by_offset(_s_last.argval) if _s_last.argval is not None else None
                                if _s_target == header or _s_target in header.predecessors:
                                    continue_map[s] = 'CONTINUE'
                                    continue
                            # [R8 fix] 区域归约算法原则 2（每块唯一归属）：
                            # 含有效用户代码（CALL/STORE/BUILD等副作用指令）的
                            # 后继块不是纯 break 目标——它是循环内 if 分支的
                            # fall-through body（如 `if x: print(...); return False`）。
                            # 真正的 break 目标块仅含跳转/清理指令（POP_TOP/JUMP等）。
                            # 将含用户代码的块误标为 BREAK 会导致：
                            # 1. has_break=True 误触发 for-else
                            # 2. AST 生成器生成 break 而非 print+return
                            # 3. print 语句丢失、return False 位置错误
                            _s_meaningful = [i for i in s.instructions
                                             if i.opname not in NOISE_OPS
                                             and i.opname not in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT',
                                                                  'JUMP_FORWARD', 'JUMP_ABSOLUTE')
                                             and i.opname not in CONDITIONAL_JUMP_OPS
                                             and i.opname not in SHORT_CIRCUIT_JUMP_OPS
                                             and i.opname not in ('POP_TOP',)]
                            if _s_meaningful:
                                # 含有效用户代码，不是纯 break 目标，跳过
                                continue
                            break_blocks_set.add(s)"""

if old_code not in content:
    print("ERROR: old_code not found in file!")
    # Try to find a unique substring
    lines = old_code.split('\n')
    for i, line in enumerate(lines):
        if line.strip() and line.strip() not in content:
            print(f"  Line {i} not found: {line.strip()}")
            break
else:
    content = content.replace(old_code, new_code)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fix applied successfully!")
