"""
单函数测试工具 - 用于逐个函数修复字节码匹配问题
"""

import sys
import os
import marshal
import tempfile
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from pycdc import decompile_pyc
from tests.bytecode_comparator import compare_bytecode_detailed
import types


def extract_function_code(pyc_path: str, func_name: str):
    """从pyc中提取函数代码对象"""
    with open(pyc_path, 'rb') as f:
        f.read(16)
        code = marshal.load(f)
    
    def find_func(c, name):
        if c.co_name == name:
            return c
        for const in c.co_consts:
            if isinstance(const, types.CodeType):
                result = find_func(const, name)
                if result:
                    return result
        return None
    
    return find_func(code, func_name)


def test_function_bytecode(orig_pyc: str, func_name: str, verbose: bool = True):
    """
    测试单个函数的字节码匹配
    
    返回: (是否匹配, 原始代码, 反编译代码, 差异报告)
    """
    # 提取原始函数代码
    orig_code = extract_function_code(orig_pyc, func_name)
    if not orig_code:
        print(f"错误: 未找到函数 {func_name}")
        return False, None, None, "函数未找到"
    
    # 反编译整个pyc
    source = decompile_pyc(orig_pyc, use_cfg=True)
    
    # 编译反编译结果
    try:
        new_code = compile(source, '<decompiled>', 'exec')
    except SyntaxError as e:
        print(f"语法错误: {e}")
        return False, orig_code, None, f"语法错误: {e}"
    
    # 在新代码中找到对应函数
    def find_func_in_code(c, name):
        if c.co_name == name:
            return c
        for const in c.co_consts:
            if isinstance(const, types.CodeType):
                result = find_func_in_code(const, name)
                if result:
                    return result
        return None
    
    new_func_code = find_func_in_code(new_code, func_name)
    if not new_func_code:
        print(f"错误: 在新代码中未找到函数 {func_name}")
        return False, orig_code, None, "新代码中未找到函数"
    
    # 对比字节码
    import dis
    orig_ins = list(dis.get_instructions(orig_code))
    new_ins = list(dis.get_instructions(new_func_code))
    
    if verbose:
        print(f"\n{'='*80}")
        print(f"函数: {func_name}")
        print(f"{'='*80}")
        print(f"原始指令数: {len(orig_ins)}")
        print(f"新指令数: {len(new_ins)}")
        
        if len(orig_ins) != len(new_ins):
            print(f"指令数量不匹配!")
        
        # 显示前20个差异
        diff_count = 0
        max_diff = 20
        for i, (o, n) in enumerate(zip(orig_ins, new_ins)):
            if o.opcode != n.opcode or o.arg != n.arg:
                if diff_count < max_diff:
                    print(f"  位置{i}: {o.opname}({o.arg}) != {n.opname}({n.arg})")
                    diff_count += 1
        
        if diff_count >= max_diff:
            print(f"  ... 还有更多信息 ...")
    
    # 检查是否匹配
    is_match = len(orig_ins) == len(new_ins)
    if is_match:
        for o, n in zip(orig_ins, new_ins):
            if o.opcode != n.opcode or o.arg != n.arg:
                is_match = False
                break
    
    if verbose:
        print(f"\n结果: {'✓ 匹配' if is_match else '✗ 不匹配'}")
    
    return is_match, orig_code, new_func_code, ""


def show_function_bytecode(pyc_path: str, func_name: str):
    """显示函数的字节码"""
    import dis
    
    code = extract_function_code(pyc_path, func_name)
    if not code:
        print(f"未找到函数: {func_name}")
        return
    
    print(f"\n{'='*80}")
    print(f"函数 {func_name} 的字节码:")
    print(f"{'='*80}")
    dis.dis(code)


def show_function_source(pyc_path: str, func_name: str):
    """显示函数的反编译源代码"""
    source = decompile_pyc(pyc_path, use_cfg=True)
    lines = source.split('\n')
    
    # 找到函数定义
    in_func = False
    func_lines = []
    indent = None
    
    for i, line in enumerate(lines):
        if f'def {func_name}(' in line:
            in_func = True
            start_idx = i
            func_lines.append(line)
            # 计算缩进
            stripped = line.lstrip()
            if stripped:
                indent = len(line) - len(stripped)
            continue
        
        if in_func:
            # 检查是否是函数结束
            if line.strip():
                current_indent = len(line) - len(line.lstrip())
                if current_indent <= indent:
                    # 函数结束
                    break
            func_lines.append(line)
    
    print(f"\n{'='*80}")
    print(f"函数 {func_name} 的反编译源代码:")
    print(f"{'='*80}")
    for line in func_lines:
        print(line)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='单函数测试工具')
    parser.add_argument('func_name', help='要测试的函数名')
    parser.add_argument('--pyc', default='python_syntax.pyc', help='PYC文件路径')
    parser.add_argument('--dis', action='store_true', help='显示字节码')
    parser.add_argument('--source', action='store_true', help='显示源代码')
    
    args = parser.parse_args()
    
    pyc_path = args.pyc
    if not os.path.isabs(pyc_path):
        pyc_path = os.path.join(project_root, pyc_path)
    
    if args.dis:
        show_function_bytecode(pyc_path, args.func_name)
    elif args.source:
        show_function_source(pyc_path, args.func_name)
    else:
        is_match, _, _, _ = test_function_bytecode(pyc_path, args.func_name)
        sys.exit(0 if is_match else 1)
