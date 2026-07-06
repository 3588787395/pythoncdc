"""
字节码对比工具 - 用于比较原始PYC和重新编译后的字节码差异
"""

import dis
import marshal
import types
import tempfile
import os
from typing import List, Tuple, Dict, Any, Optional


def compare_bytecode_detailed(orig_pyc_path: str, new_pyc_path: str) -> List[Tuple[str, str]]:
    """
    详细比较两个字节码文件的差异
    
    Args:
        orig_pyc_path: 原始PYC文件路径
        new_pyc_path: 重新编译后的PYC文件路径
        
    Returns:
        差异列表，每个元素为 (函数名, 差异描述)
    """
    diffs = []
    
    try:
        with open(orig_pyc_path, 'rb') as f:
            f.read(16)  # 跳过头部
            orig_code = marshal.load(f)
    except Exception as e:
        return [("<module>", f"无法加载原始PYC: {e}")]
    
    try:
        with open(new_pyc_path, 'rb') as f:
            f.read(16)
            new_code = marshal.load(f)
    except Exception as e:
        return [("<module>", f"无法加载新PYC: {e}")]
    
    # 提取所有函数
    orig_funcs = extract_functions(orig_code)
    new_funcs = extract_functions(new_code)
    
    # 比较每个函数
    all_func_names = set(orig_funcs.keys()) | set(new_funcs.keys())
    
    for name in sorted(all_func_names):
        if name not in orig_funcs:
            diffs.append((name, f"函数在新代码中不存在"))
            continue
        if name not in new_funcs:
            diffs.append((name, f"函数在原始代码中不存在"))
            continue
            
        orig_ins = list(dis.get_instructions(orig_funcs[name]))
        new_ins = list(dis.get_instructions(new_funcs[name]))
        
        if len(orig_ins) != len(new_ins):
            diffs.append((name, f"指令数量不同: {len(orig_ins)} vs {len(new_ins)}"))
            # 继续比较，找出具体差异
            min_len = min(len(orig_ins), len(new_ins))
            for i in range(min_len):
                if orig_ins[i].opcode != new_ins[i].opcode or orig_ins[i].arg != new_ins[i].arg:
                    diffs.append((name, f"位置{i}: {orig_ins[i].opname}({orig_ins[i].arg}) != {new_ins[i].opname}({new_ins[i].arg})"))
                    break
        else:
            for i, (o, n) in enumerate(zip(orig_ins, new_ins)):
                if o.opcode != n.opcode or o.arg != n.arg:
                    diffs.append((name, f"位置{i}: {o.opname}({o.arg}) != {n.opname}({n.arg})"))
                    break
    
    return diffs


def extract_functions(code_obj: types.CodeType, prefix: str = "") -> Dict[str, types.CodeType]:
    """
    递归提取代码对象中的所有函数
    
    Args:
        code_obj: Python代码对象
        prefix: 函数名前缀（用于嵌套函数）
        
    Returns:
        函数名字典: {函数名: 代码对象}
    """
    functions = {}
    
    # 添加当前代码对象
    name = prefix + code_obj.co_name if prefix else code_obj.co_name
    functions[name] = code_obj
    
    # 递归提取嵌套函数
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType):
            nested_name = f"{name}.{const.co_name}" if name != "<module>" else const.co_name
            functions.update(extract_functions(const, f"{nested_name}." if nested_name != const.co_name else ""))
    
    return functions


def test_decompile_and_compare(pyc_path: str, decompile_func) -> List[Tuple[str, str]]:
    """
    测试反编译并比较字节码
    
    Args:
        pyc_path: PYC文件路径
        decompile_func: 反编译函数，接收pyc_path，返回源代码字符串
        
    Returns:
        差异列表
    """
    # 反编译
    try:
        source = decompile_func(pyc_path)
    except Exception as e:
        return [("<decompilation>", f"反编译失败: {e}")]
    
    # 检查语法
    try:
        compile(source, '<decompiled>', 'exec')
    except SyntaxError as e:
        return [("<syntax>", f"语法错误: {e}")]
    
    # 重新编译并保存为PYC
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(source)
        temp_py = f.name
    
    try:
        # 编译为PYC
        import py_compile
        temp_pyc = temp_py + 'c'
        py_compile.compile(temp_py, temp_pyc, doraise=True)
        
        # 比较字节码
        diffs = compare_bytecode_detailed(pyc_path, temp_pyc)
        
        # 清理
        if os.path.exists(temp_pyc):
            os.remove(temp_pyc)
        
        return diffs
    finally:
        if os.path.exists(temp_py):
            os.remove(temp_py)


def print_diff_report(diffs: List[Tuple[str, str]], max_display: int = 50):
    """打印差异报告"""
    if not diffs:
        print("✅ 字节码完全匹配！")
        return
    
    print(f"❌ 发现 {len(diffs)} 处差异:\n")
    
    # 按函数分组
    by_func = {}
    for func, diff in diffs:
        if func not in by_func:
            by_func[func] = []
        by_func[func].append(diff)
    
    for func in sorted(by_func.keys()):
        print(f"函数: {func}")
        for diff in by_func[func][:max_display]:
            print(f"  - {diff}")
        if len(by_func[func]) > max_display:
            print(f"  ... 还有 {len(by_func[func]) - max_display} 处差异")
        print()


def analyze_pyc_with_pycdc(pyc_path: str, use_cfg: bool = True) -> Dict[str, Any]:
    """
    使用pycdc分析PYC文件
    
    Args:
        pyc_path: PYC文件路径
        use_cfg: 是否使用CFG模式
        
    Returns:
        分析结果字典
    """
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from pycdc import PycDecompiler
    import io
    
    result = {
        'success': False,
        'source': None,
        'error': None,
        'diffs': []
    }
    
    try:
        decompiler = PycDecompiler()
        if not decompiler.load_file(pyc_path):
            result['error'] = "无法加载PYC文件"
            return result
        
        output = io.StringIO()
        if decompiler.decompile(output, use_cfg=use_cfg, cfg_hybrid=True):
            source = output.getvalue()
            result['source'] = source
            result['success'] = True
            
            # 验证语法
            try:
                compile(source, '<decompiled>', 'exec')
            except SyntaxError as e:
                result['error'] = f"语法错误: {e}"
                result['success'] = False
                return result
            
            # 比较字节码
            diffs = test_decompile_and_compare(pyc_path, lambda x: source)
            result['diffs'] = diffs
        else:
            result['error'] = "反编译失败"
    except Exception as e:
        result['error'] = f"异常: {e}"
        import traceback
        result['traceback'] = traceback.format_exc()
    
    return result


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python bytecode_comparator.py <pyc文件>")
        sys.exit(1)
    
    pyc_path = sys.argv[1]
    print(f"分析文件: {pyc_path}\n")
    
    # 使用CFG模式分析
    print("=" * 60)
    print("使用CFG模式分析...")
    print("=" * 60)
    result = analyze_pyc_with_pycdc(pyc_path, use_cfg=True)
    
    if result['success']:
        print("✅ 反编译成功")
        print(f"\n源代码长度: {len(result['source'])} 字符")
        print_diff_report(result['diffs'])
    else:
        print(f"❌ 失败: {result['error']}")
        if 'traceback' in result:
            print(result['traceback'])
