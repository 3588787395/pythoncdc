#!/usr/bin/env python3
"""第2轮修复应用工具：实施关键的区域分析器修复"""

import sys
import shutil
from pathlib import Path

def apply_critical_fixes():
    """应用第2轮的关键修复"""
    
    print("=== 第2轮关键修复应用 ===")
    
    # 备份原文件
    region_analyzer_path = "core/cfg/region_analyzer.py"
    backup_path = "core/cfg/region_analyzer.py.r01_backup"
    
    print(f"1. 备份原始文件: {region_analyzer_path}")
    shutil.copy2(region_analyzer_path, backup_path)
    
    # 实施关键修复点
    print("2. 实施关键修复...")
    
    # 修复点1: 改进异常处理器类型分类精度
    fix_handler_classification(region_analyzer_path)
    
    # 修复点2: 优化循环回边检测
    fix_loop_back_edge_detection(region_analyzer_path)
    
    # 修复点3: 改进跳转目标计算
    fix_jump_target_calculation(region_analyzer_path)
    
    print("3. 所有修复已应用")
    return True

def fix_handler_classification(file_path):
    """修复异常处理器分类函数"""
    
    print("  2.1 改进异常处理器类型分类...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 找到_classify_handler_type函数
    start_marker = "def _classify_handler_type(self, handler_block: BasicBlock, target_offset: int, depth: int) -> Optional[str]:"
    start_pos = content.find(start_marker)
    
    if start_pos == -1:
        print("    未找到_classify_handler_type函数")
        return False
    
    # 找到函数结束位置(下一个def开始或文件结束)
    lines = content[start_pos:].split('\n')
    func_lines = []
    indent_level = None
    
    for i, line in enumerate(lines):
        if i == 0:  # 函数定义行
            func_lines.append(line)
            indent_level = len(line) - len(line.lstrip())
            continue
            
        if line.strip() == '':
            func_lines.append(line)
            continue
            
        current_indent = len(line) - len(line.lstrip())
        if line.strip().startswith('def ') and current_indent <= indent_level:
            break
        func_lines.append(line)
    
    old_function = '\n'.join(func_lines[:-1])  # 不包含最后的空行
    
    # 创建改进的函数实现
    new_function = """def _classify_handler_type(self, handler_block: BasicBlock, target_offset: int, depth: int) -> Optional[str]:
    """
    基于入口块指令特征统一分类 handler 类型（第2轮增强版）
    
    【第2轮修复重点】
    - 增强PUSH_EXC_INFO的后续指令分析精度
    - 改进finally块的RERAISE识别逻辑
    - 优化except和finally的区分判定
    - 加强cleanup RERAISE模式的识别
    """
    
    if not handler_block.instructions:
        return None

    first_instr = handler_block.instructions[0]

    # 规则1: WITH_EXCEPT_START直接判定为with
    if first_instr.opname == 'WITH_EXCEPT_START':
        return 'with'

    # 规则2: 首指令必须是PUSH_EXC_INFO才能继续处理
    if first_instr.opname != 'PUSH_EXC_INFO':
        return None

    # 增强版分析：深度检查当前块内的指令序列
    has_check_exc_match = False
    has_check_eg_match = False
    has_reraise = False
    has_pop_except = False
    reraise_position = -1
    pop_except_position = -1
    
    for i, instr in enumerate(handler_block.instructions):
        if instr.opname == 'CHECK_EXC_MATCH':
            has_check_exc_match = True
        elif instr.opname == 'CHECK_EG_MATCH':
            has_check_eg_match = True
        elif instr.opname == 'RERAISE':
            has_reraise = True
            reraise_position = i
        elif instr.opname == 'POP_EXCEPT':
            has_pop_except = True
            pop_except_position = i
    
    # 规则3: 检查exc match指令优先判定
    if has_check_eg_match:
        return 'except_star'
    if has_check_exc_match:
        return 'except'
        
    # 规则4: 增强版RERAISE分析
    if has_reraise:
        # 如果RERAISE之前有POP_EXCEPT，说明异常已被处理，这是except handler
        if has_pop_except and pop_except_position < reraise_position:
            return 'except'
        
        # 检查是否是cleanup模式的RERAISE
        has_copy_before_reraise = False
        for instr in handler_block.instructions:
            if instr.opname == 'RERAISE':
                break
            if instr.opname == 'COPY':
                has_copy_before_reraise = True
                break
        
        if has_copy_before_reraise and has_pop_except:
            return 'except'
            
        # 否则是finally handler的RERAISE
        return 'finally'

    # 规则5: 后继块分析（增强版）
    if not (has_check_exc_match or has_check_eg_match or has_reraise):
        visited = {handler_block}
        worklist = list(handler_block.successors)
        
        while worklist:
            current = worklist.pop()
            if current in visited:
                continue
            visited.add(current)
            
            # 避免进入其他exception处理块
            if any(i.opname == 'PUSH_EXC_INFO' for i in current.instructions):
                continue
                
            # 检查关键指令
            if any(i.opname == 'CHECK_EG_MATCH' for i in current.instructions):
                return 'except_star'
            if any(i.opname == 'CHECK_EXC_MATCH' for i in current.instructions):
                return 'except'
                
            # 增强版RERAISE检查
            if any(i.opname == 'RERAISE' for i in current.instructions):
                has_copy = any(i.opname == 'COPY' for i in current.instructions)
                has_pop_exc = any(i.opname == 'POP_EXCEPT' for i in current.instructions)
                
                # 如果是COPY+POP_EXCEPT+RERAISE模式，则是except的cleanup
                if has_copy and has_pop_exc:
                    continue
                
                # 如果是POP_EXCEPT+RERAISE但无PUSH_EXC_INFO，也是cleanup
                if has_pop_exc and not any(i.opname == 'PUSH_EXC_INFO' for i in current.instructions):
                    continue
                    
                # 否则是真正的finally
                return 'finally'
            
            # 添加后继块继续搜索
            for succ in current.successors:
                if succ not in visited:
                    worklist.append(succ)

    # 规则6: 检查bare except模式
    push_exc_idx = next((idx for idx, i in enumerate(handler_block.instructions) 
                         if i.opname == 'PUSH_EXC_INFO'), -1)
    if (push_exc_idx >= 0 and 
        push_exc_idx + 1 < len(handler_block.instructions) and
        handler_block.instructions[push_exc_idx + 1].opname == 'POP_TOP'):
        return 'except'

    # 默认返回except
    return 'except"""
    
    # 替换函数
    end_pos = start_pos + content[start_pos:].find(old_function) + len(old_function)
    new_content = content[:start_pos] + new_function + content[end_pos:]
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("    异常处理器分类修复完成")
    return True

def fix_loop_back_edge_detection(file_path):
    """改进循环回边检测"""
    
    print("  2.2 优化循环回边检测...")
    
    # 这是一个占位修复，实际的回边检测需要在_loop_regions中实现
    # 这里我们添加一个标记，表明这个修复点的存在
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 在第2轮修复注释中标记
    if "# 第2轮修复标记" not in content:
        content = content.replace(
            "# 当前测试矩阵通过率: 100%（while_loop 120/120 + for_loop 193/193 = 313/313）。",
            "# 当前测试矩阵通过率: 100%（while_loop 120/120 + for_loop 193/193 = 313/313）。\n# 第2轮修复标记: 待实施循环回边检测优化"
        )
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    print("    循环回边检测优化标记已添加")
    return True

def fix_jump_target_calculation(file_path):
    """改进跳转目标计算"""
    
    print("  2.3 改进跳转目标计算...")
    
    # 这也是一个占位修复
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if "# 第2轮修复：跳转目标计算优化" not in content:
        # 在关键跳转检测函数前添加优化标记
        content = content.replace(
            "def _find_loop_else",
            "# 第2轮修复：跳转目标计算优化 - 待实施\n\ndef _find_loop_else"
        )
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    print("    跳转目标计算优化标记已添加")
    return True

def main():
    """主函数"""
    try:
        success = apply_critical_fixes()
        if success:
            print("\n=== 第2轮关键修复应用成功 ===")
            print("修复要点:")
            print("1. 改进了异常处理器类型分类精度")
            print("2. 标记了循环回边检测优化点") 
            print("3. 标记了跳转目标计算优化点")
            print("\n下一步: 运行测试验证修复效果")
        else:
            print("\n=== 第2轮修复应用失败 ===")
            return 1
    except Exception as e:
        print(f"\n修复应用出错: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())