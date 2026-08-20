#!/usr/bin/env python3
"""第1轮修复工具：基于测试报告分析并修复关键区域"""

import sys
import dis
import marshal
import types
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def analyze_function_bytecode(pyc_path, func_name):
    """分析特定函数的字节码结构"""
    
    def load_code_from_pyc(pyc_path):
        with open(pyc_path, 'rb') as f:
            f.read(16)  # skip header
            return marshal.load(f)
    
    def find_code_by_name(code, name_path):
        """按路径查找嵌套code对象"""
        parts = name_path.split('.')
        current = code
        for part in parts:
            if part == '<module>':
                continue
            found = None
            for const in current.co_consts:
                if isinstance(const, types.CodeType) and const.co_name == part:
                    found = const
                    break
            if found is None:
                return None
            current = found
        return current
    
    orig_code = load_code_from_pyc(pyc_path)
    target_code = find_code_by_name(orig_code, func_name)
    
    if not target_code:
        print(f"未找到函数: {func_name}")
        return None
    
    print(f"\n{'='*60}")
    print(f"函数: {func_name}")
    print(f"{'='*60}")
    print(f"指令数: {len(list(dis.get_instructions(target_code)))}")
    print(f"参数个数: {target_code.co_argcount}")
    print(f"局部变量数: {target_code.co_nlocals}")
    print(f"栈大小: {target_code.co_stacksize}")
    
    instructions = list(dis.get_instructions(target_code))
    
    # 分析控制流指令
    control_flow = []
    for instr in instructions:
        if instr.opname in ['FOR_ITER', 'JUMP_FORWARD', 'JUMP_BACKWARD', 
                           'POP_JUMP_IF_FALSE', 'POP_JUMP_IF_TRUE',
                           'SETUP_FINALLY', 'WITH_EXCEPT_START', 'PUSH_EXC_INFO',
                           'POP_EXCEPT', 'RERAISE']:
            control_flow.append(instr)
    
    print(f"\n控制流指令 ({len(control_flow)}):")
    for instr in control_flow:
        print(f"  {instr.offset:4d}: {instr.opname:25s} arg={instr.arg if instr.arg is not None else 'None':>8} val={instr.argval if instr.argval is not None else '':<10}")
    
    # 分析循环结构
    loops = []
    for instr in instructions:
        if instr.opname == 'FOR_ITER':
            loops.append({
                'type': 'FOR_ITER',
                'offset': instr.offset,
                'jump_target': instr.argval,
                'jump_offset': instr.arg
            })
        elif instr.opname.startswith('JUMP_BACKWARD'):
            loops.append({
                'type': 'BACKWARD_JUMP',
                'offset': instr.offset,
                'jump_target': instr.argval,
                'jump_offset': instr.arg
            })
    
    if loops:
        print(f"\n循环结构 ({len(loops)}):")
        for loop in loops:
            print(f"  {loop['type']}: offset {loop['offset']} -> target {loop['jump_target']}")
    
    # 分析异常处理结构
    exception_handlers = []
    for instr in instructions:
        if instr.opname in ['SETUP_FINALLY', 'WITH_EXCEPT_START', 'PUSH_EXC_INFO']:
            exception_handlers.append({
                'type': instr.opname,
                'offset': instr.offset,
                'jump_target': instr.argval if instr.argval else 'N/A'
            })
    
    if exception_handlers:
        print(f"\n异常处理结构 ({len(exception_handlers)}):")
        for handler in exception_handlers:
            print(f"  {handler['type']}: offset {handler['offset']} -> target {handler['jump_target']}")
    
    return target_code

def main():
    pyc_path = "decompiler_test_comprehensive.cpython-311.pyc"
    
    print("=== 第1轮修复分析工具 ===")
    print(f"分析目标: {pyc_path}")
    
    # 分析关键问题函数
    problem_functions = [
        'validate_data',
        'exception_handling_complex'
    ]
    
    for func in problem_functions:
        analyze_function_bytecode(pyc_path, func)
    
    print("\n" + "="*60)
    print("分析结论和建议修复方向:")
    print("="*60)
    print("1. validate_data: 分析FOR_ITER循环的跳转目标和body边界")
    print("2. exception_handling_complex: 检查异常表范围和handler配对")
    print("3. 重点关注字节码偏移计算和跳转目标解析")

if __name__ == '__main__':
    main()