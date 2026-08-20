#!/usr/bin/env python3
"""第1轮测试工程师脚本：验证decompiler_test_comprehensive.cpython-311.pyc"""

import sys
import os
import json
import traceback
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def load_code_from_pyc(pyc_path):
    """从pyc文件加载代码对象"""
    import marshal
    with open(pyc_path, 'rb') as f:
        f.read(16)  # 跳过头部
        return marshal.load(f)

def extract_all_code_objects(code):
    """提取所有代码对象"""
    import types
    result = {code.co_name: code}
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            result.update(extract_all_code_objects(const))
    return result

def compare_bytecode(orig_co, decomp_co):
    """比较两个代码对象的字节码"""
    import dis
    
    orig_instrs = list(dis.get_instructions(orig_co))
    decomp_instrs = list(dis.get_instructions(decomp_co))
    
    diffs = []
    max_len = max(len(orig_instrs), len(decomp_instrs))
    
    for i in range(max_len):
        orig = orig_instrs[i] if i < len(orig_instrs) else None
        decomp = decomp_instrs[i] if i < len(decomp_instrs) else None
        
        if orig is None:
            diffs.append({
                'offset': decomp.offset if decomp else i * 2,
                'original': None,
                'decompiled': f"{decomp.opname} {decomp.argval if decomp.argval else ''}".strip()
            })
        elif decomp is None:
            diffs.append({
                'offset': orig.offset,
                'original': f"{orig.opname} {orig.argval if orig.argval else ''}".strip(),
                'decompiled': None
            })
        elif orig.opname != decomp.opname or orig.argval != decomp.argval:
            diffs.append({
                'offset': orig.offset,
                'original': f"{orig.opname} {orig.argval if orig.argval else ''}".strip(),
                'decompiled': f"{decomp.opname} {decomp.argval if decomp.argval else ''}".strip()
            })
    
    return {
        'match': len(diffs) == 0,
        'diff': diffs,
        'orig_count': len(orig_instrs),
        'decomp_count': len(decomp_instrs)
    }

def compare_pyc_files_simple(orig_pyc: str, decomp_py: str):
    """简化的pyc文件比较"""
    # 加载原始pyc
    orig_code = load_code_from_pyc(orig_pyc)
    orig_codes = extract_all_code_objects(orig_code)
    
    # 读取并编译反编译后的py文件
    with open(decomp_py, 'rb') as f:
        raw_content = f.read()
    
    # 尝试不同编码
    source = None
    for encoding in ['utf-16', 'utf-8', 'latin-1']:
        try:
            source = raw_content.decode(encoding)
            print(f"使用编码: {encoding}")
            break
        except:
            continue
    
    if source is None:
        raise Exception("无法解码反编译文件")
    
    try:
        decomp_code = compile(source, decomp_py, 'exec')
    except SyntaxError as e:
        return {
            'total_functions': len(orig_codes),
            'matched': 0,
            'mismatches': [{'function': '<module>', 'error': f'SyntaxError: {e}'}],
            'success_rate': 0.0,
            'syntax_error': str(e)
        }
    
    decomp_codes = extract_all_code_objects(decomp_code)
    
    matched = 0
    mismatches = []
    
    for name, orig_co in orig_codes.items():
        if name.startswith('<') and name.endswith('>'):
            continue  # 跳过编译器生成的名称
            
        decomp_co = decomp_codes.get(name)
        if decomp_co is None:
            mismatches.append({
                'function': name,
                'error': 'Function not found in decompiled code'
            })
            continue
        
        result = compare_bytecode(orig_co, decomp_co)
        if result['match']:
            matched += 1
        else:
            mismatches.append({
                'function': name,
                'diffs': result['diff'][:20],  # 只保留前20个差异
                'total_diffs': len(result['diff']),
                'orig_count': result['orig_count'],
                'decomp_count': result['decomp_count']
            })
    
    total = len(orig_codes)
    success_rate = (matched / total * 100) if total > 0 else 0.0
    
    return {
        'total_functions': total,
        'matched': matched,
        'mismatches': mismatches,
        'success_rate': success_rate
    }

def main():
    orig_pyc = "decompiler_test_comprehensive.cpython-311.pyc"
    decomp_py = "decompiler_test_comprehensive_decompiled_round01.py"
    
    print("=== 第1轮测试工程师报告 ===")
    print(f"目标文件: {orig_pyc}")
    print(f"反编译文件: {decomp_py}")
    
    # 检查文件存在
    if not os.path.exists(orig_pyc):
        print(f"错误: 原始pyc文件 {orig_pyc} 不存在")
        return
    
    if not os.path.exists(decomp_py):
        print(f"错误: 反编译py文件 {decomp_py} 不存在")
        return
    
    # 执行字节码比较
    try:
        print("\n1. 执行字节码比较...")
        result = compare_pyc_files_simple(orig_pyc, decomp_py)
        
        # 输出结果
        print(f"总函数数: {result['total_functions']}")
        print(f"匹配函数数: {result['matched']}")
        print(f"成功率: {result['success_rate']:.2f}%")
        print(f"不匹配函数数: {len(result['mismatches'])}")
        
        # 保存详细报告
        report_data = {
            'round': 1,
            'timestamp': '2026-08-19',
            'baseline_success_rate': 87.50,
            'current_success_rate': result['success_rate'],
            'total_functions': result['total_functions'],
            'matched_functions': result['matched'],
            'mismatched_count': len(result['mismatches']),
            'mismatches': result['mismatches'],
            'syntax_error': result.get('syntax_error')
        }
        
        # 保存报告到指定位置
        report_dir = Path(".trae/specs/decompiler-test-comprehensive-10rounds/rounds/round_01/test_engineer")
        report_dir.mkdir(parents=True, exist_ok=True)
        
        with open(report_dir / "decompile_report.md", 'w', encoding='utf-8') as f:
            f.write("# 第1轮测试工程师报告\n\n")
            f.write(f"## 测试结果摘要\n")
            f.write(f"- 测试时间: 2026-08-19\n")
            f.write(f"- 总函数数: {result['total_functions']}\n")
            f.write(f"- 匹配函数数: {result['matched']}\n")
            f.write(f"- 成功率: {result['success_rate']:.2f}%\n")
            f.write(f"- 基准成功率: 87.50%\n")
            f.write(f"- 成功率变化: {result['success_rate'] - 87.50:+.2f}%\n")
            
            if result.get('syntax_error'):
                f.write(f"\n## 语法错误\n")
                f.write(f"反编译文件存在语法错误: {result['syntax_error']}\n")
            
            if result['mismatches']:
                f.write(f"\n## 不匹配函数详情\n")
                for i, m in enumerate(result['mismatches'], 1):
                    f.write(f"\n### 不匹配函数 {i}: {m['function']}\n")
                    if 'error' in m:
                        f.write(f"- 错误: {m['error']}\n")
                    else:
                        f.write(f"- 差异总数: {m['total_diffs']}\n")
                        f.write(f"- 原始指令数: {m.get('orig_count', '?')}\n")
                        f.write(f"- 反编译指令数: {m.get('decomp_count', '?')}\n")
                        
                        # 显示前5个差异
                        if m.get('diffs'):
                            f.write(f"\n前5个差异:\n")
                            for j, diff in enumerate(m['diffs'][:5], 1):
                                orig = diff.get('original', 'N/A')
                                decomp = diff.get('decompiled', 'N/A')
                                f.write(f"  {j}. 偏移 {diff['offset']}: 原始='{orig}' 反编译='{decomp}'\n")
        
        # 保存JSON数据
        with open(report_dir / "decompile_data.json", 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n报告已保存到: {report_dir}")
        print(f"需要修复的函数数: {len(result['mismatches'])}")
        print(f"当前成功率相比基准: {result['success_rate'] - 87.50:+.2f}%")
        
        # 创建最小复现实例的目录
        repros_dir = report_dir / "minimal_repros"
        repros_dir.mkdir(exist_ok=True)
        
        # 为前10个不匹配函数创建复现实例
        for i, mismatch in enumerate(result['mismatches'][:10]):
            func_name = mismatch['function']
            repro_file = repros_dir / f"repro_r01_{i+1:02d}_{func_name.replace('.', '_')}.py"
            
            # 创建一个简单的复现实例文件
            with open(repro_file, 'w', encoding='utf-8') as f:
                f.write(f"""# 第1轮复现实例: {func_name}
# 差异数量: {mismatch.get('total_diffs', 'N/A')}
# 原始指令数: {mismatch.get('orig_count', 'N/A')}
# 反编译指令数: {mismatch.get('decomp_count', 'N/A')}

# 此文件需要进一步分析以创建最小的可复现测试案例
# 当前仅作为占位符，后续迭代中将完善为真正的最小复现实例

def placeholder():
    pass""")
        
        print(f"已创建 {min(10, len(result['mismatches']))} 个最小复现实例文件")
        
    except Exception as e:
        print(f"执行字节码比较时出错: {e}")
        traceback.print_exc()
        
        # 记录错误
        report_dir = Path(".trae/specs/decompiler-test-comprehensive-10rounds/rounds/round_01/test_engineer")
        report_dir.mkdir(parents=True, exist_ok=True)
        
        with open(report_dir / "decompile_report.md", 'w', encoding='utf-8') as f:
            f.write("# 第1轮测试工程师报告\n\n")
            f.write(f"## 错误\n")
            f.write(f"字节码比较执行失败: {e}\n")
            f.write(f"\n```\n")
            f.write(traceback.format_exc())
            f.write(f"\n```\n")

if __name__ == '__main__':
    main()