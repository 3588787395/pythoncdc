#!/usr/bin/env python3
"""
测试修复循环 - 验证修复是否成功
"""
import sys
import os
import dis
import marshal
import subprocess
import tempfile

# 添加项目路径
sys.path.insert(0, r'd:\Desktop\ptrade相关\pythoncdc')

def compare_bytecode_detailed(orig_pyc, new_pyc, target_func=None):
    """详细比较两个字节码文件"""
    with open(orig_pyc, 'rb') as f:
        f.read(16)
        orig_code = marshal.load(f)
    with open(new_pyc, 'rb') as f:
        f.read(16)
        new_code = marshal.load(f)
    
    orig_funcs = {c.co_name: c for c in orig_code.co_consts if hasattr(c, 'co_code')}
    new_funcs = {c.co_name: c for c in new_code.co_consts if hasattr(c, 'co_code')}
    
    diffs = []
    for name in orig_funcs:
        if target_func and name != target_func:
            continue
        if name in new_funcs:
            orig_ins = list(dis.get_instructions(orig_funcs[name]))
            new_ins = list(dis.get_instructions(new_funcs[name]))
            if len(orig_ins) != len(new_ins):
                diffs.append((name, f'指令数量不同: {len(orig_ins)} vs {len(new_ins)}'))
            else:
                for i, (o, n) in enumerate(zip(orig_ins, new_ins)):
                    if o.opcode != n.opcode or o.arg != n.arg:
                        diffs.append((name, f'位置{i}: {o.opname}({o.arg}) != {n.opname}({n.arg})'))
                        break
        else:
            diffs.append((name, '函数缺失'))
    return diffs

def test_file(pyc_file, func_name=None):
    """测试单个文件"""
    print(f"\n{'='*60}")
    print(f"测试文件: {pyc_file}")
    if func_name:
        print(f"目标函数: {func_name}")
    print(f"{'='*60}")
    
    # 1. 使用pycdc.py反编译
    temp_py = r'd:\Desktop\ptrade相关\pythoncdc\tests\complex\temp_output.py'
    cmd = [
        sys.executable, 
        r'd:\Desktop\ptrade相关\pythoncdc\pycdc.py',
        pyc_file,
        '-o', temp_py,
        '--cfg-hybrid'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"反编译失败: {result.stderr[:500]}")
        return False
    
    # 2. 读取反编译后的源代码
    with open(temp_py, 'r', encoding='utf-8') as f:
        source = f.read()
    
    print("\n反编译后的源代码:")
    print("-" * 40)
    print(source)
    print("-" * 40)
    
    # 3. 编译反编译后的代码
    try:
        compiled = compile(source, '<string>', 'exec')
    except SyntaxError as e:
        print(f"\n语法错误: {e}")
        print(f"行 {e.lineno}: {e.text}")
        return False
    
    # 4. 保存临时pyc文件
    temp_pyc = r'd:\Desktop\ptrade相关\pythoncdc\tests\complex\temp_output.pyc'
    with open(temp_pyc, 'wb') as f:
        import importlib.util
        f.write(importlib.util.MAGIC_NUMBER)
        f.write(b'\x00' * 12)
        marshal.dump(compiled, f)
    
    # 5. 比较字节码
    diffs = compare_bytecode_detailed(pyc_file, temp_pyc, func_name)
    
    print("\n字节码差异:")
    if diffs:
        for name, diff in diffs:
            print(f"  {name}: {diff}")
        result = False
    else:
        print("  无差异 - 字节码完全匹配!")
        result = True
    
    # 清理
    for f in [temp_py, temp_pyc]:
        if os.path.exists(f):
            os.remove(f)
    
    return result

if __name__ == '__main__':
    # 测试实例文件
    instance_file = r'd:\Desktop\ptrade相关\pythoncdc\tests\complex\__pycache__\test_instance_validate_mixed_types.cpython-311.pyc'
    
    print("="*60)
    print("测试最小实例")
    print("="*60)
    success = test_file(instance_file, 'validate_mixed_types')
    
    if success:
        print("\n最小实例测试通过!")
    else:
        print("\n最小实例测试失败!")
