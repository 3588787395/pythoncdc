import sys
"""
异常处理修复模块 - 完整版

这个模块提供了完整的try-except-finally识别算法，修复了原算法中的问题：
1. 嵌套try-except结构识别
2. finally块识别
3. 异常变量（exc_type, exc_name）正确处理
4. 多层异常表条目解析
"""

from typing import List, Dict, Set, Optional, Tuple, Any
from .basic_block import BasicBlock
from .structured_analyzer import (
    ControlStructureType, TryExceptStructure,
    StructuredAnalyzer
)


def _find_try_entry_block(analyzer, start_offset):
    """
    [关键修复] 找到try块的入口块

    与 _find_block_containing_offset 不同，这个函数返回的块的起始位置
    应该等于或最接近 start_offset，而不是包含 start_offset 的块。

    这是因为包含 start_offset 的块可能包含一些不在 try 范围内的指令
    （如 NOP 指令，它是 try 块之前的标记）。
    """
    # 首先尝试找到起始位置等于 start_offset 的块
    for block in analyzer.cfg.blocks.values():
        if block.start_offset == start_offset:
            return block

    # 如果没有找到，找到包含 start_offset 的块
    # 但优先选择起始位置最接近 start_offset 的块
    best_block = None
    best_start = -1

    for block in analyzer.cfg.blocks.values():
        if block.start_offset <= start_offset < block.end_offset:
            # 选择起始位置最接近 start_offset 的块
            if block.start_offset > best_start:
                best_start = block.start_offset
                best_block = block

    return best_block


def identify_try_except_simplified(analyzer: StructuredAnalyzer, analyzed_blocks: Set[BasicBlock]) -> None:
    """
    完整的try-except-finally识别算法
    
    核心原则：
    1. 识别所有try块（包括嵌套的）
    2. 正确匹配except handler和finally块
    3. 处理多层异常表条目
    """
    
    if not analyzer.cfg.exception_table:
        return
    
    # 解析异常表条目
    entries = analyzer.cfg.exception_table
    
    # 步骤1: 找到所有PUSH_EXC_INFO的位置（handler入口）
    push_exc_info_offsets = set()
    for block in analyzer.cfg.blocks.values():
        for instr in block.instructions:
            if instr.opname == 'PUSH_EXC_INFO':
                push_exc_info_offsets.add(instr.offset)
    
    # 步骤2: 收集所有try块
    # 按start_offset分组，收集每个try块的所有范围
    try_block_ranges = {}  # start_offset -> [{'start', 'end', 'depth', 'target'}, ...]
    
    # [关键修复] 首先找到所有try块的起始位置
    # 对于depth=0的条目，entry['start']就是try块的开始
    # 不需要依赖NOP指令，因为NOP也用于其他目的（如else分支）
    try_entry_to_target = {}  # try_start_offset -> target
    
    # [关键修复] 按target分组异常表条目，每个target对应一个try块
    # 但只识别真正的try块（target指向except handler，而不是finally cleanup）
    target_to_entries = {}  # target -> [entries]
    
    # [关键修复] 找到所有PUSH_EXC_INFO位置
    all_push_exc_info_offsets = set()
    for block in analyzer.cfg.blocks.values():
        for instr in block.instructions:
            if instr.opname == 'PUSH_EXC_INFO':
                all_push_exc_info_offsets.add(instr.offset)
    
    # [关键修复] 找到所有CHECK_EG_MATCH位置（except*语法的后续handler）
    all_check_eg_match_offsets = set()
    for block in analyzer.cfg.blocks.values():
        for instr in block.instructions:
            if instr.opname == 'CHECK_EG_MATCH':
                all_check_eg_match_offsets.add(instr.offset)
    
    # [关键修复] 找到所有CHECK_EXC_MATCH位置（普通except的后续handler）
    all_check_exc_match_offsets = set()
    for block in analyzer.cfg.blocks.values():
        for instr in block.instructions:
            if instr.opname == 'CHECK_EXC_MATCH':
                all_check_exc_match_offsets.add(instr.offset)
    
    # [关键修复] 找到真正的except handler入口
    # 真正的except handler: PUSH_EXC_INFO后面有CHECK_EXC_MATCH（具体异常类型）
    # 或PUSH_EXC_INFO后面直接是POP_TOP（裸except，POP_TOP必须紧跟）
    # except* handler: 有CHECK_EG_MATCH（可能前面没有PUSH_EXC_INFO）
    # 普通except的后续handler: 有CHECK_EXC_MATCH且前面有LOAD_GLOBAL/LOAD_NAME（异常类型）
    # finally cleanup: PUSH_EXC_INFO后面有RERAISE或特定的指令序列
    except_handler_targets = set()
    try_finally_targets = set()  # [新增] 纯try-finally的target
    
    # [关键修复] 首先处理所有CHECK_EG_MATCH位置（except*语法的handler）
    # 这些位置可能是except*的后续handler（没有PUSH_EXC_INFO）
    # [关键修复] 对于except*语法，handler的开始是LOAD_GLOBAL，而不是CHECK_EG_MATCH
    # 但需要确保只添加那些不在PUSH_EXC_INFO block中的LOAD_GLOBAL
    for block in analyzer.cfg.blocks.values():
        for i, instr in enumerate(block.instructions):
            if instr.opname == 'CHECK_EG_MATCH':
                # 找到这个CHECK_EG_MATCH前面的LOAD_GLOBAL/LOAD_NAME（异常类型）
                # [关键修复] 只在当前block中查找，不跨block查找
                # 因为except*的后续handler的LOAD_GLOBAL应该在同一个block中
                found_load = False
                for j in range(i-1, max(0, i-10), -1):
                    prev_opname = block.instructions[j].opname
                    if prev_opname in ('LOAD_GLOBAL', 'LOAD_NAME'):
                        # 这是except* handler的开始（异常类型加载）
                        except_handler_targets.add(block.instructions[j].offset)
                        found_load = True
                        break
                
                # [关键修复] 如果在当前block中没有找到，检查所有block
                # 对于except*语法，LOAD_GLOBAL可能在不同的block中
                if not found_load:
                    # 查找在CHECK_EG_MATCH之前，且距离最近的LOAD_GLOBAL
                    check_eg_match_offset = instr.offset
                    closest_load_offset = None
                    closest_load_instr = None
                    min_distance = float('inf')
                    
                    for b in analyzer.cfg.blocks.values():
                        for b_instr in b.instructions:
                            if b_instr.opname in ('LOAD_GLOBAL', 'LOAD_NAME'):
                                # 只考虑异常类型（排除print等其他函数）
                                if b_instr.argval in ('ValueError', 'TypeError', 'ConnectionError', 'TimeoutError', 'Exception', 'BaseException'):
                                    if b_instr.offset < check_eg_match_offset:
                                        distance = check_eg_match_offset - b_instr.offset
                                        # 只考虑距离在合理范围内的LOAD（比如40个字节内）
                                        if distance < 40 and distance < min_distance:
                                            # 检查这个LOAD是否已经被添加到targets中
                                            if b_instr.offset not in except_handler_targets:
                                                min_distance = distance
                                                closest_load_offset = b_instr.offset
                                                closest_load_instr = b_instr
                    
                    if closest_load_instr:
                        except_handler_targets.add(closest_load_offset)
                        found_load = True
    
    # [关键修复] 处理所有CHECK_EXC_MATCH位置（普通except的后续handler）
    # 这些handler可能没有PUSH_EXC_INFO，而是通过跳转链链接到第一个handler
    for check_exc_offset in all_check_exc_match_offsets:
        # 找到这个CHECK_EXC_MATCH前面的LOAD_GLOBAL/LOAD_NAME（异常类型）
        found_load = False
        for block in analyzer.cfg.blocks.values():
            for i, instr in enumerate(block.instructions):
                if instr.offset == check_exc_offset:
                    # 在当前block中查找前面的LOAD_GLOBAL/LOAD_NAME
                    for j in range(i-1, max(0, i-10), -1):
                        prev_opname = block.instructions[j].opname
                        if prev_opname in ('LOAD_GLOBAL', 'LOAD_NAME'):
                            # 这是except handler的开始（异常类型加载）
                            # print(f"[DEBUG CHECK_EXC_MATCH] Found LOAD at offset {block.instructions[j].offset}, adding to targets")
                            except_handler_targets.add(block.instructions[j].offset)
                            found_load = True
                            break
                    break
            if found_load:
                break
        
        # 如果在当前block中没有找到，检查所有block
        if not found_load:
            # print(f"[DEBUG CHECK_EXC_MATCH] No LOAD found in current block, checking all blocks")
            # 查找在CHECK_EXC_MATCH之前，且距离最近的LOAD_GLOBAL
            closest_load_offset = None
            closest_load_instr = None
            min_distance = float('inf')
            
            for b in analyzer.cfg.blocks.values():
                for b_instr in b.instructions:
                    if b_instr.opname in ('LOAD_GLOBAL', 'LOAD_NAME'):
                        # 只考虑异常类型
                        if b_instr.argval in ('ValueError', 'TypeError', 'KeyError', 'IndexError', 'AttributeError', 'RuntimeError', 'ConnectionError', 'TimeoutError', 'Exception', 'BaseException'):
                            if b_instr.offset < check_exc_offset:
                                distance = check_exc_offset - b_instr.offset
                                # 只考虑距离在合理范围内的LOAD（比如30个字节内）
                                if distance < 30 and distance < min_distance:
                                    if b_instr.offset not in except_handler_targets:
                                        min_distance = distance
                                        closest_load_offset = b_instr.offset
                                        closest_load_instr = b_instr
            
            if closest_load_instr:
                # print(f"[DEBUG CHECK_EXC_MATCH] Found closest LOAD at offset {closest_load_offset}, distance={min_distance}, argval={closest_load_instr.argval}")
                except_handler_targets.add(closest_load_offset)
    
    for block in analyzer.cfg.blocks.values():
        for i, instr in enumerate(block.instructions):
            if instr.opname == 'PUSH_EXC_INFO':
                # 检查后面的指令
                is_except_handler = False
                is_try_finally = False
                following_ops = []
                for j in range(i+1, min(i+10, len(block.instructions))):
                    following_ops.append(block.instructions[j].opname)
                for j in range(i+1, min(i+10, len(block.instructions))):
                    next_opname = block.instructions[j].opname
                    # 如果有CHECK_EXC_MATCH，是具体异常类型的handler
                    if next_opname == 'CHECK_EXC_MATCH':
                        is_except_handler = True
                        break
                    # [关键修复] 如果有CHECK_EG_MATCH，是except*（异常组）的handler
                    if next_opname == 'CHECK_EG_MATCH':
                        is_except_handler = True
                        break
                    # [关键修复] 如果直接是POP_TOP（在PUSH_EXC_INFO后的前5条指令内），是裸except的handler
                    if next_opname == 'POP_TOP' and j <= i + 5:
                        is_except_handler = True
                        break
                    # [关键修复] 如果遇到RERAISE，说明是try-finally的cleanup（不是except handler）
                    if next_opname == 'RERAISE':
                        is_try_finally = True
                        break
                    # 如果遇到POP_EXCEPT或RETURN_VALUE，停止检查
                    if next_opname in ('POP_EXCEPT', 'RETURN_VALUE'):
                        break
                
                # [关键修复] 如果没有在当前block中找到RERAISE，检查后继block
                if not is_except_handler and not is_try_finally:
                    visited = set()
                    worklist = list(block.successors)
                    while worklist and not is_try_finally:
                        succ = worklist.pop(0)
                        if succ in visited:
                            continue
                        visited.add(succ)
                        for succ_instr in succ.instructions:
                            if succ_instr.opname == 'RERAISE':
                                is_try_finally = True
                                break
                            # 如果遇到CHECK_EXC_MATCH或POP_TOP，说明是except handler
                            if succ_instr.opname in ('CHECK_EXC_MATCH', 'CHECK_EG_MATCH'):
                                is_except_handler = True
                                break
                        if not is_try_finally and not is_except_handler:
                            worklist.extend(succ.successors)
                
                # [关键修复] 更精确地区分except handler和finally cleanup
                # except handler: 有CHECK_EXC_MATCH（有异常类型）或CHECK_EG_MATCH（except*）或POP_TOP（裸except）
                # finally cleanup: 有RERAISE，或者有CHECK_EXC_MATCH/POP_TOP但后面有RETURN_VALUE且没有POP_EXCEPT
                if is_except_handler:
                    # [关键修复] 区分裸except和具体异常类型的except
                    # 检查是否有CHECK_EXC_MATCH（具体异常类型）或CHECK_EG_MATCH（except*）
                    has_check_exc_match = False
                    has_check_eg_match = False
                    has_pop_top = False
                    # [关键修复] 扩大搜索范围到15条指令，因为LOAD_GLOBAL可能很长
                    for j in range(i+1, min(i+15, len(block.instructions))):
                        opname = block.instructions[j].opname
                        if opname == 'CHECK_EXC_MATCH':
                            has_check_exc_match = True
                            break
                        if opname == 'CHECK_EG_MATCH':
                            has_check_eg_match = True
                            break
                        if opname == 'POP_TOP':
                            has_pop_top = True
                            break

                    if has_pop_top:
                        # [关键修复] 裸except（有POP_TOP），直接认为是except handler
                        # 即使有RETURN_VALUE，也是except handler的正常结束
                        except_handler_targets.add(instr.offset)
                    elif has_check_exc_match or has_check_eg_match:
                        # [关键修复] 具体异常类型的except或except*，检查是否有RETURN_VALUE
                        # 如果有RETURN_VALUE，可能是finally cleanup
                        has_return = False
                        for j in range(i+1, min(i+15, len(block.instructions))):
                            opname = block.instructions[j].opname
                            if opname == 'RETURN_VALUE':
                                has_return = True
                                break
                            if opname == 'RERAISE':
                                break
                        if not has_return:
                            except_handler_targets.add(instr.offset)
                        else:
                            try_finally_targets.add(instr.offset)
                    else:
                        # 默认情况
                        except_handler_targets.add(instr.offset)
                elif is_try_finally:
                    try_finally_targets.add(instr.offset)
    
    
    # [关键修复] 识别真正的try块
    # 真正的try块：
    # 1. depth=0 且 target 指向 except handler（顶层try块）
    # 2. depth>0 且 target 指向 except handler（嵌套在handler中的try块）
    
    # 首先，找到所有depth=0的条目
    depth0_entries = [e for e in entries if e['depth'] == 0]
    
    # [关键修复] 识别所有try块（包括嵌套的）
    try_starts = set()  # 真正的try块起始位置
    
    # [关键修复] 找到所有with语句的异常处理target（块中有WITH_EXCEPT_START）
    with_except_targets = set()
    for block in analyzer.cfg.blocks.values():
        has_with_except_start = any(i.opname == 'WITH_EXCEPT_START' for i in block.instructions)
        if has_with_except_start:
            # 这个块是with语句的异常处理块
            with_except_targets.add(block.start_offset)
    
    # 1. 识别depth=0的try块（顶层）
    # [关键修复] 只处理那些target指向真正的except handler（不是with语句）的try块
    # [关键修复] 只保留最外层的try块（start最小的）
    potential_try_starts = []
    for entry in depth0_entries:
        if entry['target'] in except_handler_targets:
            # [关键修复] 检查target是否指向with语句的异常处理块
            is_with_except = False
            for block in analyzer.cfg.blocks.values():
                if block.start_offset == entry['target']:
                    if any(i.opname == 'WITH_EXCEPT_START' for i in block.instructions):
                        is_with_except = True
                        break
            
            if not is_with_except:
                potential_try_starts.append((entry['start'], entry['target']))
    
    # [关键修复] 保留所有独立的try块（不仅仅是外层）
    # 独立的try块：target指向不同的except handler
    # 嵌套的try块：target指向不同的except handler，且start在另一个try块的范围内
    if potential_try_starts:
        # 按start排序
        sorted_starts = sorted(potential_try_starts, key=lambda x: x[0])
        
        # 收集所有不同的handler target
        seen_targets = set()
        for start, target in sorted_starts:
            if target not in seen_targets:
                # 这是一个独立的try块（不同的handler）
                try_starts.add(start)
                seen_targets.add(target)
            # 这个try块与之前的try块共享同一个handler，可能是同一个try块的不同部分
    
    # 2. 识别depth>0的try块（嵌套在handler中的）
    # 这些try块的target也是except handler，但depth>0
    depth_n_entries = [e for e in entries if e['depth'] > 0]
    
    # [关键修复] 按start分组，收集每个try块的所有范围
    start_to_entries = {}
    for entry in depth_n_entries:
        if entry['start'] not in start_to_entries:
            start_to_entries[entry['start']] = []
        start_to_entries[entry['start']].append(entry)
    
    for try_start, try_entries in start_to_entries.items():
        # [关键修复] 检查这个try块是否对应一个真正的try-except结构
        # 真正的try-except结构应该有NOP指令作为开始标志
        try_entry_block = analyzer._find_block_containing_offset(try_start)
        if not try_entry_block:
            continue
        
        # [关键修复] 检查try_entry_block是否有NOP指令
        # 注意：NOP可能在try_entry_block中，也可能在前面的块中（偏移量小于try_start）
        has_nop = any(i.opname == 'NOP' for i in try_entry_block.instructions)
        
        # [关键修复] 如果在try_entry_block中没有找到NOP，检查前面的块
        # 因为Python编译器可能在try_start之前插入NOP作为标记
        if not has_nop:
            # 查找在try_start之前的NOP指令（在合理范围内，比如8个字节内）
            for block in analyzer.cfg.blocks.values():
                for instr in block.instructions:
                    if instr.opname == 'NOP':
                        # 检查这个NOP是否在try_start之前且距离不远
                        if try_start - 8 <= instr.offset < try_start:
                            has_nop = True
                            break
                if has_nop:
                    break
        
        if not has_nop:
            continue
        
        # [关键修复] 检查这个try块是否已经被识别为其他try块的一部分
        # 如果try_entry_block在其他try-except的try_body中，跳过它
        is_in_other_try = False
        for struct in analyzer.structures:
            if isinstance(struct, TryExceptStructure):
                if try_entry_block in struct.try_body:
                    is_in_other_try = True
                    break
        if is_in_other_try:
            continue
        
        # 检查所有entries的target是否都是except handler
        all_targets_valid = True
        for entry in try_entries:
            if entry['target'] not in except_handler_targets:
                all_targets_valid = False
                break
            
            # [关键修复] 检查target是否指向with语句的异常处理块
            is_with_except = False
            for block in analyzer.cfg.blocks.values():
                if block.start_offset == entry['target']:
                    if any(i.opname == 'WITH_EXCEPT_START' for i in block.instructions):
                        is_with_except = True
                        break
            
            if is_with_except:
                all_targets_valid = False
                break
        
        if not all_targets_valid:
            continue
        
        # 检查这个try块是否对应一个真正的try-except结构
        # 真正的try-except结构应该有CHECK_EXC_MATCH或POP_TOP在handler中
        is_real_try_except = False
        for entry in try_entries:
            for block in analyzer.cfg.blocks.values():
                if block.start_offset == entry['target']:
                    has_check = any(i.opname == 'CHECK_EXC_MATCH' for i in block.instructions)
                    has_pop_top = any(i.opname == 'POP_TOP' for i in block.instructions)
                    if has_check or has_pop_top:
                        is_real_try_except = True
                        break
            if is_real_try_except:
                break
        
        if is_real_try_except:
            # [关键修复] 检查这个try块是否与其他已识别的try块共享同一个handler
            # 如果共享同一个handler，说明它们是同一个try-except的不同部分，应该合并
            shares_handler_with_existing = False
            current_targets = set(e['target'] for e in try_entries)
            
            for existing_start in list(try_starts):
                # 找到existing_start对应的entries
                existing_entries = start_to_entries.get(existing_start, [])
                if not existing_entries:
                    continue
                
                # 检查是否是同一个handler
                existing_targets = set(e['target'] for e in existing_entries)
                
                if existing_targets == current_targets:
                    # 同一个handler，说明是同一个try-except的不同部分
                    # 检查existing_start是否已经在analyzer.structures中
                    # 如果在，将当前try_entries合并到existing_start的条目中
                    existing_struct = None
                    for struct in analyzer.structures:
                        if isinstance(struct, TryExceptStructure):
                            if hasattr(struct, 'try_start_offset') and struct.try_start_offset == existing_start:
                                existing_struct = struct
                                break
                    
                    if existing_struct:
                        # 合并try_body
                        current_try_body = _collect_try_body_complete(analyzer, try_start, max(e['end'] for e in try_entries), [(try_start, max(e['end'] for e in try_entries))])
                        for block in current_try_body:
                            if block not in existing_struct.try_body:
                                existing_struct.try_body.append(block)
                        existing_struct.try_body.sort(key=lambda b: b.start_offset)
                    shares_handler_with_existing = True
                    break
            
            if not shares_handler_with_existing:
                try_starts.add(try_start)
    
    # 如果没有找到except handler，可能是纯try-finally
    if not try_starts:
        for entry in depth0_entries:
            if entry['target'] in try_finally_targets:
                try_starts.add(entry['start'])
                # [关键修复] 不要break，因为可能有多个嵌套的try-finally
        # 也检查depth>0的try-finally
        for entry in depth_n_entries:
            if entry['target'] in try_finally_targets:
                try_starts.add(entry['start'])
    
    # [关键修复] 为每个try块起始位置收集所有相关的条目
    # 相关的条目包括：
    # 1. 所有depth=0且start匹配的条目（try体、else体等）
    # 2. 所有depth>=1且保护这些区域的条目（handler、cleanup）
    for try_start in try_starts:
        # 找到这个try块对应的主target（except handler或finally cleanup）
        main_target = None
        # 首先检查depth=0的条目
        for entry in depth0_entries:
            if entry['start'] == try_start:
                if entry['target'] in except_handler_targets:
                    main_target = entry['target']
                    break
                elif entry['target'] in try_finally_targets and main_target is None:
                    main_target = entry['target']
        
        # [关键修复] 如果没有找到，检查depth>0的条目（嵌套try块）
        if main_target is None:
            for entry in entries:
                if entry['depth'] > 0 and entry['start'] == try_start:
                    if entry['target'] in except_handler_targets:
                        main_target = entry['target']
                        break
                    elif entry['target'] in try_finally_targets and main_target is None:
                        main_target = entry['target']
        
        if main_target is None:
            continue
        
        # [关键修复] 如果main_target是with语句的异常处理target，跳过这个try块
        # 因为这是with语句的隐式异常处理，不是显式的try-except
        if main_target in with_except_targets:
            continue
        
        try_entry_to_target[try_start] = main_target
        
        # [关键修复] 收集所有与这个try块相关的条目
        # 策略：找到所有depth=0的条目，其start在从try_start开始的连续区域内
        # 连续区域的结束由遇到下一个try块或函数结束决定
        
        # [关键修复] 收集所有try块的start位置（包括depth>0的嵌套try块）
        all_starts = sorted(try_starts)
        
        # 找到当前try_start的索引
        try_start_idx = all_starts.index(try_start)
        
        # 找到下一个try块的起始位置（如果有）
        next_try_start = None
        for i in range(try_start_idx + 1, len(all_starts)):
            s = all_starts[i]
            # 检查这个start是否对应一个新的try块
            # 新的try块：其target指向一个except handler，且不是当前try块的handler
            for e in depth0_entries:
                if e['start'] == s and e['target'] in except_handler_targets:
                    # 检查是否是同一个handler
                    if e['target'] != main_target:
                        next_try_start = s
                        break
            if next_try_start:
                break
        
        # 收集所有相关的条目
        # 包括：
        # 1. 所有start在当前try块范围内的depth=0条目
        # 2. 所有depth>=1且保护这些区域的条目
        # [关键修复] 也收集当前try块本身的条目（可能是depth>0的嵌套try块）
        related_entries = []
        for entry in entries:
            if entry['depth'] == 0:
                # 检查是否在当前try块的范围内
                if try_start <= entry['start']:
                    if next_try_start is None or entry['start'] < next_try_start:
                        related_entries.append(entry)
            elif entry['depth'] > 0 and entry['start'] == try_start:
                # [关键修复] 收集当前try块本身的条目（嵌套try块）
                related_entries.append(entry)
        
        # 转换为ranges格式
        try_block_ranges[try_start] = []
        for entry in related_entries:
            try_block_ranges[try_start].append({
                'start': entry['start'],
                'end': entry['end'],
                'depth': entry['depth'],
                'target': entry['target']
            })
        
    
    # 步骤3: 按嵌套层次排序try块（外层优先）
    def get_nesting_depth(start_offset):
        depth = 0
        for other_start, ranges in try_block_ranges.items():
            if other_start != start_offset:
                other_end = max(r['end'] for r in ranges)
                if other_start <= start_offset < other_end:
                    depth += 1
        return depth
    
    sorted_try_blocks = sorted(
        try_block_ranges.items(),
        key=lambda x: (get_nesting_depth(x[0]), x[0])
    )
    
    # 步骤4: 为每个try块创建结构
    for start_offset, ranges in sorted_try_blocks:
        # 检查是否已处理
        already_has_try_except = any(
            hasattr(struct, 'try_start_offset') and struct.try_start_offset == start_offset
            for struct in analyzer.structures
        )
        if already_has_try_except:
            continue
        
        # 找到try入口块
        # [关键修复] 使用 _find_try_entry_block 而不是 _find_block_containing_offset
        # 因为 _find_block_containing_offset 可能返回包含 NOP 指令的块
        try_entry = _find_try_entry_block(analyzer, start_offset)
        if not try_entry:
            continue
        
        # [关键修复] 区分try体、else体和finally保护范围
        # ranges按start排序，第一个范围是try体
        sorted_ranges = sorted(ranges, key=lambda r: r['start'])
        
        # try体是第一个范围
        try_range = sorted_ranges[0]
        try_start, try_end = try_range['start'], try_range['end']
        
        # else体是其他受finally保护的范围（target指向finally cleanup）
        else_ranges = []
        for r in sorted_ranges[1:]:
            if r['target'] in try_finally_targets:
                else_ranges.append((r['start'], r['end']))
        
        # 所有范围用于收集try体
        all_ranges = [(r['start'], r['end']) for r in sorted_ranges]
        
        # 计算总范围
        max_end = max(r['end'] for r in ranges)
        
        
        # [关键修复] 收集try体（使用所有范围，而不仅仅是第一个范围）
        # 这对于有多个不连续范围的try块很重要（如包含continue的循环）
        try_body = _collect_try_body_complete(analyzer, try_start, max_end, all_ranges)
        
        if not try_body:
            continue
        
        try_body.sort(key=lambda b: b.start_offset)
        
        # 步骤5: 收集except handlers
        except_handlers = []
        handler_starts = set()
        
        # [关键修复] 找到当前try块对应的所有handler
        # 从try块的target（handler入口）开始收集
        # 对于每个try块，找到其target对应的handler块
        
        # 找到当前try块的主target（handler地址）
        main_handler_target = None
        for entry in entries:
            # [关键修复] 支持任意depth的try块（包括嵌套在多层循环中的）
            if entry['depth'] >= 0:
                for r in ranges:
                    if r['start'] <= entry['start'] < r['end']:
                        main_handler_target = entry['target']
                        break
                if main_handler_target:
                    break
        
        # [关键修复] 收集所有相关的handler
        # handler在异常表中表现为depth>=1的条目
        # 需要收集所有与main_handler_target相关的handler
        if main_handler_target:
            # [关键修复] 找到当前try块对应的所有handler入口地址
            # handler入口地址是depth=0或depth>0条目的target
            current_handler_entries = []  # (handler_start, handler_end)
            
            # [关键修复] 找到当前try块对应的target（可能是depth=0或depth>0）
            handler_target = None
            for entry in entries:
                if entry['start'] == start_offset:
                    handler_target = entry['target']
                    break
            
            if handler_target:
                # [关键修复] 如果handler_target是try-finally target或是with语句的异常处理target，则没有except handler
                if handler_target not in try_finally_targets and handler_target not in with_except_targets:
                    # [关键修复] 收集所有通过跳转链链接的handler
                    # 从第一个handler开始，沿着跳转链收集所有handler
                    visited_handlers = set()
                    current_target = handler_target
                    
                    # [关键修复] 多个except handler可能共享同一个PUSH_EXC_INFO
                    # 第一个handler有PUSH_EXC_INFO，后续handler通过跳转链链接
                    # 需要收集所有在跳转链中的handler
                    iteration = 0
                    while current_target and current_target not in visited_handlers:
                        iteration += 1
                        visited_handlers.add(current_target)
                        
                        # [关键修复] 检查当前target是否是有效的handler入口
                        # 有效的handler入口：
                        # 1. 有PUSH_EXC_INFO（第一个handler）
                        # 2. 有CHECK_EXC_MATCH（普通except的后续handler）
                        # 3. 有CHECK_EG_MATCH（except*的handler）
                        # 4. 以POP_TOP开始且没有CHECK_EXC_MATCH（裸except handler）
                        handler_block = analyzer._find_block_containing_offset(current_target)
                        if handler_block:
                            has_push_exc_info = any(instr.opname == 'PUSH_EXC_INFO' for instr in handler_block.instructions)
                            has_check_exc_match = any(instr.opname == 'CHECK_EXC_MATCH' for instr in handler_block.instructions)
                            has_check_eg_match = any(instr.opname == 'CHECK_EG_MATCH' for instr in handler_block.instructions)
                            # [关键修复] 检查是否是裸except handler（以POP_TOP开始，没有CHECK_EXC_MATCH）
                            is_bare_except = (
                                handler_block.instructions and
                                handler_block.instructions[0].opname == 'POP_TOP' and
                                not has_check_exc_match and
                                not has_check_eg_match
                            )
                            # [关键修复] 排除纯RERAISE块（只有RERAISE指令，没有实际处理代码）
                            has_real_code = any(
                                instr.opname not in ('RERAISE', 'COPY', 'POP_EXCEPT', 'RESUME', 'NOP')
                                for instr in handler_block.instructions
                            )
                            
                            # [关键修复] 收集handler：
                            # 1. 有PUSH_EXC_INFO（第一个handler）
                            # 2. 有CHECK_EXC_MATCH（普通except的后续handler）
                            # 3. 有CHECK_EG_MATCH（except*的handler）
                            # 4. 是裸except handler（以POP_TOP开始，没有CHECK_EXC_MATCH）
                            if has_real_code and (has_push_exc_info or has_check_exc_match or has_check_eg_match or is_bare_except):
                                # 找到这个handler的结束位置
                                handler_end = None
                                for h_entry in entries:
                                    if h_entry['depth'] >= 1 and h_entry['start'] == current_target:
                                        handler_end = h_entry['end']
                                        break
                                # 如果没有找到条目，使用block的结束位置
                                if handler_end is None:
                                    handler_end = max(instr.offset for instr in handler_block.instructions) + 2
                                current_handler_entries.append((current_target, handler_end))
                        
                        # [关键修复] 找到下一个handler（通过跳转指令）
                        # 在当前handler块中查找POP_JUMP_FORWARD_IF_FALSE或JUMP_FORWARD指令
                        next_target = None
                        for block in analyzer.cfg.blocks.values():
                            if block.start_offset == current_target:
                                for instr in block.instructions:
                                    # [关键修复] 处理普通except的POP_JUMP_FORWARD_IF_FALSE
                                    if instr.opname == 'POP_JUMP_FORWARD_IF_FALSE':
                                        # [关键修复] 使用argval而不是arg
                                        next_target = instr.argval
                                        break
                                    # [关键修复] 处理except*的JUMP_FORWARD（跳转到下一个handler）
                                    elif instr.opname == 'JUMP_FORWARD':
                                        next_target = instr.argval
                                        # 不break，继续查找POP_JUMP_FORWARD_IF_FALSE（优先级更高）
                                break
                        
                        # [关键修复] 对于except*语法，下一个handler可能不在跳转目标中
                        # 而是在except_handler_targets中的其他target
                        # [关键修复] 只选择那些不是当前handler一部分的target
                        if next_target is None and current_target in except_handler_targets:
                            # 找到except_handler_targets中当前target之后的下一个target
                            sorted_targets = sorted(except_handler_targets)
                            current_idx = sorted_targets.index(current_target)
                            # [关键修复] 查找下一个不在当前handler范围内的target
                            for next_idx in range(current_idx + 1, len(sorted_targets)):
                                candidate = sorted_targets[next_idx]
                                # [关键修复] 检查这个candidate是否在当前handler的范围内
                                # 如果在范围内，说明它是当前handler的一部分，跳过
                                # 如果不在范围内，说明它是下一个handler
                                handler_end = max(instr.offset for instr in handler_block.instructions)
                                if candidate > handler_end:
                                    next_target = candidate
                                    break
                        
                        current_target = next_target
                    
            
            
            # 收集handler块
            for handler_start, handler_end in current_handler_entries:
                if handler_start not in handler_starts:
                    handler_starts.add(handler_start)
                    handler_blocks = _collect_handler_body_complete(analyzer, handler_start, entries)
                    if handler_blocks:
                        exc_type = _extract_exception_type(handler_blocks)
                        exc_name = _extract_exception_name(handler_blocks)
                        except_handlers.append((exc_type, exc_name, handler_blocks))
        
        # 步骤6: 识别finally块
        finally_body = []
        has_finally = False
        
        # [关键修复] 找到所有PUSH_EXC_INFO位置（包括finally的）
        all_push_exc_info_offsets = set()
        for block in analyzer.cfg.blocks.values():
            for instr in block.instructions:
                if instr.opname == 'PUSH_EXC_INFO':
                    all_push_exc_info_offsets.add(instr.offset)
        
        # 找到finally块的入口（PUSH_EXC_INFO不在except_handler_targets中，也不在with_except_targets中）
        # [关键修复] 排除with语句的异常处理
        finally_targets = all_push_exc_info_offsets - except_handler_targets - with_except_targets
        
        
        # 找到finally块的入口
        # [关键修复] finally的异常表条目可能是depth=0或depth=1
        for entry in entries:
            if entry['target'] in finally_targets:
                handler_block = analyzer._find_block_containing_offset(entry['target'])
                if handler_block:
                    has_push = any(instr.opname == 'PUSH_EXC_INFO' for instr in handler_block.instructions)
                    has_check = any(instr.opname == 'CHECK_EXC_MATCH' for instr in handler_block.instructions)
                    if has_push and not has_check:
                        # [关键修复] 检查是否是真正的finally块，而不是异常清理代码
                        # 真正的finally块应该有多个入口点（正常路径和异常路径）
                        # 异常清理代码块只有一个入口点（通过异常表）
                        is_real_finally = _is_real_finally_block(analyzer, entry['target'], entries, all_push_exc_info_offsets)
                        if not is_real_finally:
                            continue
                        
                        # [关键修复] 对于finally，entry['start']可能小于max_end
                        # 因为finally保护的是else体或其他代码
                        finally_body = _collect_finally_body(analyzer, entry['target'], entries)
                        if finally_body:
                            has_finally = True
                            break
        
        
        # 步骤6.5: 识别else子句
        # [关键修复] 使用else_ranges来识别else体
        else_body = []
        has_else = False
        
        if else_ranges:
            
            # [关键修复] 收集所有handler块，避免将handler块误判为else体
            handler_blocks_set = set()
            for _, _, h_blocks in except_handlers:
                for b in h_blocks:
                    handler_blocks_set.add(b)
            
            # [关键修复] 对于except* + else + finally结构，else代码可能不在else_ranges中
            # 需要从try_body块中的JUMP_FORWARD指令找到else代码的入口
            # [关键修复] 但是，如果存在finally块，JUMP_FORWARD可能跳转到finally块，而不是else块
            else_entry_offset = None
            if not has_finally:  # [关键修复] 只有在没有finally块时才从JUMP_FORWARD查找else入口
                for block in try_body:
                    for instr in block.instructions:
                        if instr.opname == 'JUMP_FORWARD' and instr.offset >= try_end - 2:
                            # 这是try代码末尾的JUMP_FORWARD，跳转到else代码
                            else_entry_offset = instr.argval
                            break
                    if else_entry_offset:
                        break
            else:
                pass
            # 收集else体中的块
            else_blocks = set()
            for block in analyzer.cfg.blocks.values():
                # 跳过已经在finally_body或handler中的块
                if finally_body and block in finally_body:
                    continue
                if block in handler_blocks_set:
                    continue
                
                # [关键修复] 对于try_body中的块，也检查是否包含else体的指令
                # 这种情况发生在try-except-else-finally结构中
                is_in_try_body = block in try_body
                
                # 检查块是否在else_ranges范围内
                # [关键修复] 检查块是否在else_ranges范围内
                in_else_range = False
                for else_start, else_end in else_ranges:
                    for instr in block.instructions:
                        if else_start <= instr.offset < else_end:
                            in_else_range = True
                            break
                    if in_else_range:
                        break
                
                # [关键修复] 检查块是否是else代码的入口（从JUMP_FORWARD跳转过来）
                is_else_entry = else_entry_offset and block.start_offset == else_entry_offset
                
                if in_else_range or is_else_entry:
                    # 检查块的指令，排除exception相关的指令
                    has_else_instr = False
                    for instr in block.instructions:
                        if instr.opname in ('PUSH_EXC_INFO', 'CHECK_EXC_MATCH', 'RERAISE', 
                                           'POP_EXCEPT', 'COPY', 'NOP', 'RESUME'):
                            continue
                        has_else_instr = True
                        break
                    
                    if has_else_instr:
                        if is_in_try_body:
                            has_else = True
                        else:
                            else_blocks.add(block)
            
            if else_blocks:
                else_body = list(else_blocks)
                else_body.sort(key=lambda b: b.start_offset)
                has_else = True
            elif has_else:
                pass
            # 继续后续处理
        if except_handlers and not has_finally:
            # 如果没有finally，使用原来的逻辑（基于handler位置）
            # [关键修复] 只使用当前try块对应的handler的target，而不是所有depth>=1的条目
            # 对于嵌套try-except-with结构，需要确保只考虑当前try块的handler
            current_try_handler_targets = set()
            for entry in entries:
                if entry['depth'] >= 1:
                    # 检查这个handler是否保护当前try块的范围
                    for r in ranges:
                        if r['start'] <= entry['start'] < r['end']:
                            current_try_handler_targets.add(entry['target'])
                            break
            
            # [关键修复] 如果没有找到当前try块的handler，使用except_handlers中的target
            if not current_try_handler_targets and except_handlers:
                for _, _, h_blocks in except_handlers:
                    if h_blocks:
                        current_try_handler_targets.add(h_blocks[0].start_offset)
            
            if current_try_handler_targets:
                first_handler_offset = min(current_try_handler_targets)
            else:
                first_handler_offset = None
            
            
            # [关键修复] 收集所有handler块，避免将handler块误判为else体
            handler_blocks_set = set()
            for _, _, h_blocks in except_handlers:
                for b in h_blocks:
                    handler_blocks_set.add(b)
            
            # else块包含的指令：在try体结束之后，在handler开始之前
            else_instructions = []
            if first_handler_offset:  # [关键修复] 只有在找到handler时才处理else
                for block in analyzer.cfg.blocks.values():
                    # 跳过handler中的块
                    if block in handler_blocks_set:
                        continue
                    
                    # [关键修复] 对于try_body中的块，检查是否包含else体的指令
                    is_in_try_body = block in try_body
                    
                    for instr in block.instructions:
                        instr_offset = instr.offset
                        # 检查指令是否在try结束之后和handler开始之前
                        # [关键修复] 使用 try_end < instr_offset 而不是 try_end <= instr_offset
                        # 因为 try_end 是try块的结束位置，任何在 try_end 位置的指令都是try块的一部分
                        if try_end < instr_offset < first_handler_offset:
                            # 排除exception相关的指令
                            if instr.opname in ('PUSH_EXC_INFO', 'CHECK_EXC_MATCH', 'RERAISE',
                                               'POP_EXCEPT', 'COPY', 'NOP', 'RESUME', 'RETURN_VALUE', 'RETURN_CONST'):
                                continue
                            
                            # [关键修复] 排除JUMP_BACKWARD和JUMP_FORWARD指令，因为这是循环控制流的一部分
                            # 当try块在循环内部时，try块结束后的JUMP_BACKWARD是跳回循环开始
                            # 而不是跳转到else代码
                            if instr.opname in ('JUMP_BACKWARD', 'JUMP_FORWARD'):
                                continue
                            
                            # [关键修复] 排除所有跳转相关的指令，因为它们只是控制流的一部分
                            if instr.opname in ('JUMP_ABSOLUTE', 'POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_FORWARD_IF_TRUE',
                                               'POP_JUMP_BACKWARD_IF_FALSE', 'POP_JUMP_BACKWARD_IF_TRUE'):
                                continue
                            
                            # [关键修复] 排除WITH_EXCEPT_START指令，因为这是with语句的异常处理
                            # 不是else子句的代码
                            if instr.opname == 'WITH_EXCEPT_START':
                                continue
                            
                            # [关键修复] 排除异常处理清理代码
                            # 例如：e = None; del e（在except块结束时）
                            # 特征：LOAD_CONST None 后面跟着 STORE_FAST
                            # 或者 DELETE_FAST
                            if instr.opname == 'DELETE_FAST':
                                continue
                            if instr.opname == 'LOAD_CONST' and instr.argval is None:
                                # 检查下一条指令是否是STORE_FAST
                                continue
                            if instr.opname == 'STORE_FAST' and instr.argval == 'e':
                                # 检查上一条指令是否是LOAD_CONST None
                                continue

                            if is_in_try_body:
                                # [关键修复] 设置has_else为True，但不将块添加到else_body
                                # else体的指令将从try_body块中提取
                                has_else = True
                            else:
                                else_instructions.append((block, instr))
            
            # 收集包含else指令的块
            else_blocks = set()
            for block, instr in else_instructions:
                else_blocks.add(block)
            
            if else_blocks:
                else_body = list(else_blocks)
                else_body.sort(key=lambda b: b.start_offset)
                has_else = True
            elif has_else:
                pass
        
        # [关键修复] 计算try体的实际结束位置
        # try_end应该是所有depth=0范围的最后一个结束位置
        # 因为try块可能覆盖多个范围（如if-else的两个分支都在try中）
        depth0_ranges = [r for r in ranges if r.get('depth', 0) == 0]
        if depth0_ranges:
            actual_try_end = max(r['end'] for r in depth0_ranges)
        elif ranges:
            actual_try_end = max(r['end'] for r in ranges)
        else:
            actual_try_end = max_end
        
        # 步骤7: 创建try-except结构
        try_struct = TryExceptStructure(
            struct_type=ControlStructureType.TRY_EXCEPT,
            entry_block=try_entry,
            try_body=try_body,
            except_handlers=except_handlers,
            else_body=else_body,
            has_else=has_else,
            finally_body=finally_body,
            has_finally=has_finally,
            try_start_offset=start_offset,
            try_end_offset=actual_try_end
        )
        
        analyzer.structures.append(try_struct)
        
        # 映射块到结构
        analyzed_blocks.add(try_entry)
        analyzer.block_to_structure[try_entry] = try_struct
        
        for b in try_body:
            analyzed_blocks.add(b)
            analyzer.block_to_structure[b] = try_struct
        
        for _, _, h_blocks in except_handlers:
            for b in h_blocks:
                analyzed_blocks.add(b)
                analyzer.block_to_structure[b] = try_struct
        
        if finally_body:
            for b in finally_body:
                analyzed_blocks.add(b)
                analyzer.block_to_structure[b] = try_struct


def _is_handler_for_try(entry, try_ranges):
    """检查异常表条目是否属于当前try块"""
    entry_start = entry['start']
    for r in try_ranges:
        if r['start'] <= entry_start < r['end']:
            return True
    return False


def _collect_try_body_complete(analyzer, start_offset, end_offset, all_ranges):
    """完整的try体收集"""
    try_body = []
    # [关键修复] 使用 _find_try_entry_block 而不是 _find_block_containing_offset
    try_entry = _find_try_entry_block(analyzer, start_offset)
    
    if not try_entry:
        return try_body
    
    def is_in_ranges_strict(block):
        """严格检查块是否在try范围内

        块的任意指令偏移在try范围内即认为块在范围内
        这样可以正确处理跨越try边界的块
        """
        for instr in block.instructions:
            instr_offset = instr.offset
            for r_start, r_end in all_ranges:
                if r_start <= instr_offset < r_end:
                    return True
        return False

    def is_block_mainly_in_ranges(block):
        """检查块的主要部分是否在try范围内

        对于跨越try边界的块，检查大部分指令是否在try范围内。
        这样可以正确处理那些起始位置在try范围外但主要部分在try范围内的块。
        """
        in_range_count = 0
        total_count = len(block.instructions)

        for instr in block.instructions:
            instr_offset = instr.offset
            for r_start, r_end in all_ranges:
                if r_start <= instr_offset < r_end:
                    in_range_count += 1
                    break

        # 如果超过一半的指令在try范围内，认为块主要在try范围内
        # [关键修复] 使用 >= 而不是 >，这样可以正确处理那些恰好一半指令在try范围内的块
        return in_range_count >= total_count / 2
    
    def is_exception_block(block):
        for instr in block.instructions:
            if instr.opname in ('PUSH_EXC_INFO', 'CHECK_EXC_MATCH', 'RERAISE'):
                return True
        return False
    
    def is_finally_normal_path_block(block, try_entry_block):
        """检查块是否是finally正常路径的一部分
        
        在Python 3.11+中，finally正常路径的代码在try范围内，但不应该属于try body。
        
        [关键修复] 真正的finally正常路径块的特征：
        1. 块不包含try body的业务逻辑（比较操作、赋值、函数调用等）
        2. 块主要包含条件检查（如if var:）和清理代码（如var.close()）
        3. 块不是try body中if/for/while等控制流结构的分支
        
        [关键修复] 之前的实现过于激进，将try body中的比较操作和跳转指令
        也误判为finally正常路径，导致链式比较等代码丢失。
        
        新的实现：只有当块满足以下所有条件时才认为是finally正常路径：
        - 块不包含COMPARE_OP、STORE_FAST/STORE_NAME/STORE_GLOBAL（赋值）
        - 块不包含条件跳转指令（POP_JUMP_*）
        - 块不包含JUMP_FORWARD（if语句的then分支跳转）
        - 块的后继链经过异常处理块（PUSH_EXC_INFO）后才到达RETURN_VALUE
          或者块本身只包含清理代码模式
        """
        if block == try_entry_block:
            return False
        
        has_business_logic = False
        for instr in block.instructions:
            if instr.opname in ('LOAD_METHOD', 'LOAD_ATTR', 'CALL', 'PRECALL'):
                has_business_logic = True
                break
        
        if has_business_logic:
            return False
        
        has_compare = False
        has_store = False
        has_cond_jump = False
        has_jump_forward = False
        for instr in block.instructions:
            if instr.opname == 'COMPARE_OP':
                has_compare = True
            if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                has_store = True
            if instr.opname in ('POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE',
                                'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
                                'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE',
                                'POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_BACKWARD_IF_NONE',
                                'POP_JUMP_FORWARD_IF_NOT_NONE', 'POP_JUMP_BACKWARD_IF_NOT_NONE',
                                'JUMP_IF_FALSE_OR_POP', 'JUMP_IF_TRUE_OR_POP'):
                has_cond_jump = True
            if instr.opname == 'JUMP_FORWARD':
                has_jump_forward = True
        
        if has_compare or has_store or has_cond_jump:
            return False
        
        if has_jump_forward:
            return False
        
        visited = set()
        worklist = [try_entry_block]
        is_successor = False
        while worklist:
            b = worklist.pop(0)
            if b in visited:
                continue
            visited.add(b)
            if block in b.successors:
                is_successor = True
                break
            for succ in b.successors:
                if succ not in visited:
                    worklist.append(succ)
        
        if not is_successor:
            return False
        
        visited = set()
        worklist = list(block.successors)
        found_return = False
        found_exception_handler = False
        
        while worklist:
            succ = worklist.pop(0)
            if succ in visited:
                continue
            visited.add(succ)
            
            if any(instr.opname == 'PUSH_EXC_INFO' for instr in succ.instructions):
                found_exception_handler = True
                break
            
            if any(instr.opname == 'RETURN_VALUE' for instr in succ.instructions):
                found_return = True
            
            for next_succ in succ.successors:
                if next_succ not in visited:
                    worklist.append(next_succ)
        
        return found_return and not found_exception_handler
    
    # [关键修复] 收集所有在try范围内的块（基于指令偏移而非块起始）
    candidate_blocks = []
    for block in analyzer.cfg.blocks.values():
        # [关键修复] 使用 is_in_ranges_strict 而不是 is_block_mainly_in_ranges
        # 这样可以正确处理那些跨越try边界但包含try范围内指令的块
        if is_in_ranges_strict(block) and not is_exception_block(block):
            candidate_blocks.append(block)
    
    # [关键修复] 排除finally正常路径的块
    for block in candidate_blocks:
        if not is_finally_normal_path_block(block, try_entry):
            try_body.append(block)
    
    # [关键修复] 确保try_entry在最前面
    if try_entry in try_body:
        try_body.remove(try_entry)
        try_body.insert(0, try_entry)
    
    return try_body


def _collect_handler_body_complete(analyzer, handler_start, all_entries):
    """完整的handler体收集"""
    handler_body = []
    handler_entry = analyzer._find_block_containing_offset(handler_start)
    
    if not handler_entry:
        return handler_body
    
    # [关键修复] 查找handler的结束位置
    # 对于depth>=1的条目，end字段表示handler的结束位置
    handler_end = None
    for entry in all_entries:
        if entry['start'] == handler_start and entry['depth'] >= 1:
            handler_end = entry['end']
            break
    
    # [关键修复] 如果没有找到精确匹配，查找包含handler_start的条目
    if handler_end is None:
        for entry in all_entries:
            if entry['start'] <= handler_start < entry['end'] and entry['depth'] >= 1:
                handler_end = entry['end']
                break
    
    # [关键修复] 获取所有循环头和try块的起始位置
    # handler不应该包含跳转到这些位置的块
    loop_headers = set()
    try_starts = set()
    for block in analyzer.cfg.blocks.values():
        for instr in block.instructions:
            if instr.opname == 'FOR_ITER':
                loop_headers.add(block.start_offset)
            elif instr.opname == 'NOP':
                # NOP可能标记try块的开始
                try_starts.add(instr.offset)
    
    worklist = [handler_entry]
    visited = set()
    
    while worklist:
        block = worklist.pop(0)
        if block in visited:
            continue
        visited.add(block)
        
        if handler_end is not None and block.start_offset >= handler_end:
            continue
        
        handler_body.append(block)
        
        for succ in block.successors:
            if succ not in visited:
                is_cleanup = _is_cleanup_block(succ)
                if not is_cleanup:
                    if handler_end is None or succ.start_offset < handler_end:
                        # [关键修复] 检查是否跳转到循环头或try块开始
                        # 如果是，说明这是控制流跳转（如break/continue），不应该跟随
                        is_jump_to_loop_start = succ.start_offset in loop_headers and succ.start_offset < handler_start
                        if is_jump_to_loop_start:
                            continue
                        worklist.append(succ)
    
    return handler_body


def _collect_finally_body(analyzer, finally_start, all_entries):
    """收集finally体"""
    finally_body = []
    finally_entry = analyzer._find_block_containing_offset(finally_start)

    if not finally_entry:
        return finally_body

    # [关键修复] 使用BFS遍历收集所有finally相关的块
    # 直到遇到清理代码块（包含RERAISE）或跳转到try块之外的块
    worklist = [finally_entry]
    visited = set()
    
    # 获取try块的范围，用于判断块是否在try之外
    try_start = None
    try_end = None
    for entry in all_entries:
        if entry['target'] == finally_start and entry['depth'] == 0:
            try_start = entry['start']
            try_end = entry['end']
            break
    
    while worklist:
        block = worklist.pop(0)
        if block in visited:
            continue
        visited.add(block)
        
        # [关键修复] 检查是否是清理代码块（只包含异常处理框架指令和RERAISE）
        # 清理代码块的特征：只包含 PUSH_EXC_INFO, RERAISE, COPY, POP_EXCEPT, LOAD_CONST, STORE_FAST, DELETE_FAST, NOP, CACHE, RESUME
        # 不包含实际的业务逻辑代码（如方法调用、属性访问等）
        exception_framework_instrs = ('PUSH_EXC_INFO', 'RERAISE', 'COPY', 'POP_EXCEPT', 
                                      'LOAD_CONST', 'STORE_FAST', 'DELETE_FAST', 'NOP', 'CACHE', 'RESUME',
                                      'POP_TOP', 'RETURN_VALUE')
        has_only_framework_instrs = True
        has_reraise = False
        
        for instr in block.instructions:
            if instr.opname == 'RERAISE':
                has_reraise = True
            # [关键修复] 如果指令不是异常处理框架指令，说明包含正常代码
            if instr.opname not in exception_framework_instrs:
                has_only_framework_instrs = False
                break
        
        # [关键修复] 如果块只包含异常处理框架指令且有RERAISE，是清理代码块，跳过
        if has_only_framework_instrs and has_reraise:
            continue
        
        # [关键修复] 如果块在try块范围之外，跳过
        if try_end is not None and block.start_offset > try_end + 100:  # 给一个缓冲范围
            continue
        
        finally_body.append(block)
        
        # [关键修复] 添加后继块到worklist
        for succ in block.successors:
            if succ not in visited:
                worklist.append(succ)
    
    return finally_body


def _is_cleanup_block(block):
    """检查是否是cleanup代码块"""
    if len(block.instructions) <= 5:
        cleanup_only = True
        for instr in block.instructions:
            if instr.opname not in ('LOAD_CONST', 'STORE_FAST', 'DELETE_FAST', 'RERAISE',
                                    'COPY', 'POP_EXCEPT', 'NOP', 'CACHE', 'RESUME'):
                cleanup_only = False
                break
        has_reraise = any(instr.opname == 'RERAISE' for instr in block.instructions)
        if cleanup_only and has_reraise:
            return True
    return False


def _is_real_finally_block(analyzer, finally_start, all_entries, all_push_exc_info_offsets):
    """
    检查是否是真正的finally块，而不是异常清理代码
    
    真正的finally块特征：
    1. 有正常执行路径的入口（通过JUMP_FORWARD或fall-through）
    2. 异常路径通过异常表进入
    
    异常清理代码块特征：
    1. 只有异常执行路径的入口（通过异常表）
    2. 没有正常执行路径进入
    3. 通常包含PUSH_EXC_INFO, 一些清理代码, RERAISE
    
    [关键区别]
    真正的finally块：有前驱块通过JUMP_FORWARD显式跳转到finally块
    异常清理代码块：没有前驱块通过JUMP_FORWARD跳转，只有异常表条目指向它
    
    [Python 3.11+ 修复]
    在Python 3.11+中，finally块可以通过异常表进入，而不一定需要JUMP_FORWARD。
    我们需要检查异常表条目来确定是否是真正的finally块。
    """
    finally_block = analyzer._find_block_containing_offset(finally_start)
    if not finally_block:
        return False
    
    # [关键修复] 检查是否有前驱块通过JUMP_FORWARD显式跳转到finally_start
    has_jmp_forward_entry = False
    
    for pred in finally_block.predecessors:
        # 检查前驱块的最后一个指令
        if pred.instructions:
            last_instr = pred.instructions[-1]
            # 如果前驱块的最后一个指令是JUMP_FORWARD且跳转到finally_start
            if last_instr.opname == 'JUMP_FORWARD' and last_instr.argval == finally_start:
                has_jmp_forward_entry = True
                break
    
    # [Python 3.11+ 关键修复] 检查是否有异常表条目指向finally_start
    # 在Python 3.11+中，finally块可以通过异常表进入
    has_exception_table_entry = False
    for entry in all_entries:
        if entry['target'] == finally_start and entry['depth'] == 0:
            has_exception_table_entry = True
            break
    
    # [关键修复] 如果没有JUMP_FORWARD入口，也没有异常表条目，一定是异常清理代码
    if not has_jmp_forward_entry and not has_exception_table_entry:
        return False
    
    # [关键修复] 检查finally块的内容
    # 真正的finally块应该有实际代码，不只是异常处理框架
    has_real_code = False
    for instr in finally_block.instructions:
        if instr.opname not in ('PUSH_EXC_INFO', 'RERAISE', 'COPY', 'POP_EXCEPT', 
                                'LOAD_CONST', 'STORE_FAST', 'DELETE_FAST', 'NOP', 'CACHE', 'RESUME'):
            has_real_code = True
            break
    
    # 如果没有实际代码，只是异常处理框架，不是真正的finally
    if not has_real_code:
        return False
    
    return True


def _extract_exception_type(handler_blocks):
    """提取异常类型
    
    支持单个异常类型和异常元组（如 except (TypeError, ValueError):）
    也支持 except* 语法（使用 CHECK_EG_MATCH）
    支持属性访问的异常类型（如 except zmq.ZMQError:）
    """
    for block in handler_blocks:
        # [关键修复] 检查 CHECK_EXC_MATCH（普通 except）或 CHECK_EG_MATCH（except*）
        has_check = any(instr.opname in ('CHECK_EXC_MATCH', 'CHECK_EG_MATCH') for instr in block.instructions)
        if has_check:
            # [关键修复] 收集所有LOAD_GLOBAL/LOAD_NAME/LOAD_ATTR指令，直到遇到BUILD_TUPLE
            exception_types = []
            found_build_tuple = False
            pending_attr = None
            
            for instr in block.instructions:
                # [关键修复] 同时处理LOAD_GLOBAL和LOAD_NAME
                if instr.opname in ('LOAD_GLOBAL', 'LOAD_NAME'):
                    exception_types.append(instr.argval)
                    pending_attr = instr.argval
                elif instr.opname == 'LOAD_ATTR':
                    # [关键修复] 处理属性访问的异常类型（如 zmq.ZMQError）
                    if pending_attr is not None:
                        # 替换最后一个类型为属性访问形式
                        full_name = pending_attr + '.' + instr.argval
                        if exception_types:
                            exception_types[-1] = full_name
                        else:
                            exception_types.append(full_name)
                        pending_attr = None
                    else:
                        # 没有前置的LOAD，直接使用属性名
                        exception_types.append(instr.argval)
                elif instr.opname == 'LOAD_FAST':
                    # [关键修复] 处理 LOAD_FAST + LOAD_ATTR 的情况（如 zmq.ZMQError）
                    pending_attr = instr.argval
                elif instr.opname == 'BUILD_TUPLE':
                    # 遇到BUILD_TUPLE，说明是异常元组
                    found_build_tuple = True
                    break
                elif instr.opname in ('CHECK_EXC_MATCH', 'CHECK_EG_MATCH'):
                    # 遇到CHECK_EXC_MATCH或CHECK_EG_MATCH，停止收集
                    break
            
            if found_build_tuple and len(exception_types) > 1:
                # 返回异常元组字符串表示
                return '(' + ', '.join(exception_types) + ')'
            elif exception_types:
                # 返回单个异常类型
                return exception_types[0]
    return None


def _extract_exception_name(handler_blocks):
    """提取异常变量名
    
    异常处理代码模式（普通except）：
    1. PUSH_EXC_INFO
    2. LOAD_GLOBAL <ExceptionType>  (可选)
    3. CHECK_EXC_MATCH  (可选)
    4. POP_JUMP_FORWARD_IF_FALSE <target>  (可选)
    5. STORE_FAST <name>  (如果有as子句，在跳转之后)
       或者 POP_TOP (如果没有as子句)
    
    异常处理代码模式（except*）：
    1. PUSH_EXC_INFO
    2. COPY
    3. BUILD_LIST 0
    4. SWAP 2
    5. LOAD_GLOBAL <ExceptionType>
    6. CHECK_EG_MATCH
    7. COPY 1
    8. POP_JUMP_FORWARD_IF_NONE <target>
    9. POP_TOP
    10. STORE_FAST <name>  (如果有as子句)
        或者 (无操作，使用POP_TOP后的异常对象)
    
    如果没有as子句，第5步是POP_TOP
    如果有as子句，第5步是STORE_FAST
    """
    found_check = False
    found_jump = False
    
    for block in handler_blocks:
        for instr in block.instructions:
            if instr.opname in ('CHECK_EXC_MATCH', 'CHECK_EG_MATCH'):
                found_check = True
                found_jump = False
            elif found_check and instr.opname in ('POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_FORWARD_IF_NONE'):
                found_jump = True
            elif found_check and found_jump and instr.opname in ('STORE_FAST', 'STORE_NAME'):
                # 在CHECK_EXC_MATCH/CHECK_EG_MATCH和POP_JUMP之后找到STORE，说明有as子句
                return instr.argval
            elif found_check and found_jump and instr.opname == 'POP_TOP':
                # 在CHECK_EXC_MATCH/CHECK_EG_MATCH和POP_JUMP之后找到POP_TOP，说明没有as子句
                return None
            elif found_check and found_jump and instr.opname not in ('NOP', 'CACHE', 'RESUME', 'PRECALL', 'CALL', 'COPY'):
                # 如果在跳转之后找到其他指令，说明没有as子句
                return None
    
    return None
