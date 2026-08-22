#!/usr/bin/env python3
"""
Round 01 测试框架
反编译 pyc 文件 → 编译 → 字节码比对 → 报告
"""
import sys
import os
import marshal
import types
import dis
import json
import traceback
import io
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from pycdc import decompile_pyc


def load_code_from_pyc(pyc_path):
    """从pyc文件加载code对象"""
    with open(pyc_path, 'rb') as f:
        magic = f.read(4)
        flags = int.from_bytes(f.read(4), 'little')
        if flags & 0x1:
            f.read(8)
        else:
            f.read(8)
        code = marshal.load(f)
    return code


def extract_all_code_objects(code, prefix=''):
    """递归提取所有code对象"""
    result = {}
    if code.co_name == '<module>':
        name = '<module>'
    else:
        name = prefix + '.' + code.co_name if prefix else code.co_name
    result[name] = code
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            child_prefix = name if name != '<module>' else ''
            result.update(extract_all_code_objects(const, child_prefix))
    return result


def normalize_instructions(code):
    """规范化指令序列"""
    instrs = []
    for instr in dis.get_instructions(code):
        if instr.opname in ('RESUME', 'NOP', 'CACHE', 'EXTENDED_ARG'):
            continue
        argval = instr.argval
        if isinstance(argval, types.CodeType):
            argval_str = '<code>'
        elif isinstance(argval, str) and ('\\' in argval and '.py' in argval):
            argval_str = '<filepath>'
        else:
            argval_str = str(argval)
        # [R01 fix] 先收集原始序列，再做上下文敏感规范化
        opname = instr.opname
        instrs.append((opname, argval_str))
    return _normalize_attr_method(instrs)


def _normalize_attr_method(instrs):
    """对称上下文规范化：LOAD_ATTR 后随 CALL 视为方法形式(≈LOAD_METHOD)。

    本语料 py c由非标准 3.11 编译器产生：普通方法调用 obj.m() 用了
    LOAD_ATTR 而非 LOAD_METHOD。两侧同规则转换，保持比较公平：
    - with a.b:      （无调用）→ 保持 LOAD_ATTR
    - with a.b(c):   （有调用）→ 双侧都归一为 LOAD_METHOD
    """
    result = []
    n = len(instrs)
    for i, (opname, argval) in enumerate(instrs):
        if opname == 'LOAD_ATTR':
            # 向前看：遇到边界(STORE/JUMP/RETURN)或超过窗口则停止
            has_call = False
            for j in range(i + 1, min(i + 16, n)):
                op2 = instrs[j][0]
                if op2 in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF',
                           'RETURN_VALUE', 'RETURN_CONST', 'POP_JUMP_FORWARD_IF_FALSE',
                           'POP_JUMP_FORWARD_IF_TRUE', 'JUMP_FORWARD', 'JUMP_ABSOLUTE',
                           'BEFORE_WITH'):
                    break
                if op2 == 'CALL':
                    has_call = True
                    break
            if has_call:
                opname = 'LOAD_METHOD'
        result.append((opname, argval))
    return result


def compare_code_objects(orig_code, decomp_code, name=''):
    """比较两个code对象的字节码，返回匹配详情"""
    orig_instrs = normalize_instructions(orig_code)
    decomp_instrs = normalize_instructions(decomp_code)
    
    if orig_instrs == decomp_instrs:
        return {'match': True, 'name': name, 'orig_len': len(orig_instrs), 'decomp_len': len(decomp_instrs)}
    
    # 找出第一个不同的位置
    diff_pos = 0
    for i in range(min(len(orig_instrs), len(decomp_instrs))):
        if orig_instrs[i] != decomp_instrs[i]:
            diff_pos = i
            break
    else:
        diff_pos = min(len(orig_instrs), len(decomp_instrs))
    
    # 收集差异上下文
    context_start = max(0, diff_pos - 3)
    context_end = min(max(len(orig_instrs), len(decomp_instrs)), diff_pos + 5)
    
    diff_context = []
    for i in range(context_start, context_end):
        o = orig_instrs[i] if i < len(orig_instrs) else ('<MISSING>', '')
        d = decomp_instrs[i] if i < len(decomp_instrs) else ('<MISSING>', '')
        marker = '  ' if o == d else '**'
        diff_context.append(f'{marker} [{i}] ORIG: {o[0]} {o[1][:60]} | DECP: {d[0]} {d[1][:60]}')
    
    return {
        'match': False,
        'name': name,
        'orig_len': len(orig_instrs),
        'decomp_len': len(decomp_instrs),
        'diff_pos': diff_pos,
        'diff_context': diff_context,
    }


def test_single_pyc(pyc_path):
    """测试单个pyc文件的反编译质量"""
    result = {
        'path': pyc_path,
        'success': False,
        'total_funcs': 0,
        'matched_funcs': 0,
        'match_rate': 0.0,
        'errors': [],
        'diffs': [],
    }
    
    # 1. 加载原始字节码
    try:
        orig_code = load_code_from_pyc(pyc_path)
    except Exception as e:
        result['errors'].append(f'加载pyc失败: {e}')
        return result
    
    # 2. 反编译
    try:
        decomp_source = decompile_pyc(pyc_path)
        if not decomp_source or not decomp_source.strip():
            result['errors'].append('反编译结果为空')
            return result
    except Exception as e:
        result['errors'].append(f'反编译失败: {e}')
        traceback.print_exc()
        return result
    
    # 3. 去掉头部注释行
    lines = decomp_source.split('\n')
    while lines and (lines[0].startswith('#') or lines[0].strip() == ''):
        lines.pop(0)
    clean_source = '\n'.join(lines)
    
    # 4. 编译反编译结果
    try:
        decomp_code = compile(clean_source, '<decompiled>', 'exec')
    except SyntaxError as e:
        result['errors'].append(f'语法错误: {e.msg} at line {e.lineno}')
        result['errors'].append(f'源码片段: {clean_source.split(chr(10))[e.lineno-1:e.lineno+2] if e.lineno else "N/A"}')
        return result
    except Exception as e:
        result['errors'].append(f'编译失败: {e}')
        return result
    
    # 5. 提取所有函数
    orig_funcs = extract_all_code_objects(orig_code)
    decomp_funcs = extract_all_code_objects(decomp_code)
    
    result['total_funcs'] = len(orig_funcs)
    
    # 6. 逐一比对
    for name, orig_func in orig_funcs.items():
        if name not in decomp_funcs:
            result['diffs'].append({'name': name, 'error': '函数缺失'})
            continue
        
        cmp = compare_code_objects(orig_func, decomp_funcs[name], name)
        if cmp['match']:
            result['matched_funcs'] += 1
        else:
            result['diffs'].append(cmp)
    
    result['match_rate'] = result['matched_funcs'] / result['total_funcs'] if result['total_funcs'] > 0 else 1.0
    result['success'] = result['match_rate'] >= 1.0
    
    return result


def batch_test(pyc_files, max_files=None):
    """批量测试pyc文件"""
    results = []
    total = len(pyc_files)
    if max_files:
        pyc_files = pyc_files[:max_files]
    
    for i, pyc_path in enumerate(pyc_files):
        print(f'[{i+1}/{len(pyc_files)}] Testing: {os.path.basename(pyc_path)}', flush=True)
        r = test_single_pyc(pyc_path)
        results.append(r)
        status = '✓' if r['success'] else f'{r["match_rate"]:.1%}'
        print(f'  -> {status} ({r["matched_funcs"]}/{r["total_funcs"]} funcs)', flush=True)
    
    return results


def generate_report(results, output_path):
    """生成测试报告"""
    total = len(results)
    passed = sum(1 for r in results if r['success'])
    failed = total - passed
    avg_rate = sum(r['match_rate'] for r in results) / total if total else 0
    
    lines = []
    lines.append(f'# 反编译测试报告')
    lines.append(f'')
    lines.append(f'- 总计: {total}')
    lines.append(f'- 通过: {passed} ({passed/total:.1%})')
    lines.append(f'- 失败: {failed} ({failed/total:.1%})')
    lines.append(f'- 平均匹配率: {avg_rate:.4f}')
    lines.append(f'')
    
    # 失败列表按匹配率排序
    fails = sorted([r for r in results if not r['success']], key=lambda x: x['match_rate'])
    if fails:
        lines.append(f'## 失败文件 (按匹配率升序)')
        lines.append(f'')
        lines.append(f'| 匹配率 | 函数匹配 | 文件 |')
        lines.append(f'|--------|---------|------|')
        for r in fails[:50]:
            short_path = r['path'].split('site-packages/')[-1] if 'site-packages/' in r['path'] else os.path.basename(r['path'])
            lines.append(f'| {r["match_rate"]:.2%} | {r["matched_funcs"]}/{r["total_funcs"]} | {short_path} |')
        lines.append(f'')
    
    # 详细差异（前5个最差文件）
    if fails:
        lines.append(f'## 详细差异 (前5个最差文件)')
        lines.append(f'')
        for r in fails[:5]:
            short_path = r['path'].split('site-packages/')[-1] if 'site-packages/' in r['path'] else os.path.basename(r['path'])
            lines.append(f'### {short_path} ({r["match_rate"]:.2%})')
            if r['errors']:
                for e in r['errors']:
                    lines.append(f'- 错误: {e}')
            for d in r['diffs'][:5]:
                if 'error' in d:
                    lines.append(f'- 函数 {d["name"]}: {d["error"]}')
                else:
                    lines.append(f'- 函数 {d["name"]}: diff@{d.get("diff_pos","?")}')
                    for ctx in d.get('diff_context', []):
                        lines.append(f'  {ctx}')
            lines.append(f'')
    
    report = '\n'.join(lines)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    return report


def get_all_pyc_files(site_packages_dir):
    """获取site-packages下所有pyc文件"""
    pyc_files = []
    for root, dirs, files in os.walk(site_packages_dir):
        for f in files:
            if f.endswith('.pyc'):
                pyc_files.append(os.path.join(root, f))
    return sorted(pyc_files)


def save_ok_py(pyc_path, decomp_source):
    """保存OK.py文件"""
    ok_path = pyc_path.replace('.pyc', 'OK.py')
    # 去掉头部注释
    lines = decomp_source.split('\n')
    while lines and (lines[0].startswith('#') or lines[0].strip() == ''):
        lines.pop(0)
    clean_source = '\n'.join(lines)
    with open(ok_path, 'w', encoding='utf-8') as f:
        f.write(clean_source)
    return ok_path


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--single', help='测试单个pyc文件')
    parser.add_argument('--batch', action='store_true', help='批量测试所有pyc')
    parser.add_argument('--max', type=int, help='最多测试N个文件')
    parser.add_argument('--output', default='round01_report.md', help='报告输出路径')
    parser.add_argument('--save-ok', action='store_true', help='对通过的文件保存OK.py')
    args = parser.parse_args()
    
    site_dir = os.path.join(HERE, 'site-packages')
    
    if args.single:
        r = test_single_pyc(args.single)
        print(json.dumps({k: v for k, v in r.items() if k != 'diffs'}, indent=2, ensure_ascii=False))
        if r['diffs']:
            print(f'\n差异详情 ({len(r["diffs"])})个函数):')
            for d in r['diffs'][:10]:
                if 'error' in d:
                    print(f'  {d["name"]}: {d["error"]}')
                else:
                    print(f'  {d["name"]}: diff@{d.get("diff_pos","?")}')
                    for ctx in d.get('diff_context', []):
                        print(f'    {ctx}')
        if args.save_ok and r['success']:
            decomp_source = decompile_pyc(args.single)
            ok_path = save_ok_py(args.single, decomp_source)
            print(f'Saved OK.py: {ok_path}')
    elif args.batch:
        pyc_files = get_all_pyc_files(site_dir)
        print(f'Found {len(pyc_files)} pyc files')
        results = batch_test(pyc_files, args.max)
        report = generate_report(results, args.output)
        print(f'\nReport saved to: {args.output}')
    else:
        parser.print_help()
