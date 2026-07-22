#!/usr/bin/env python3
"""Phase 0.2: 失败用例字节码 diff 分析与算法根因映射

对 baseline_failures.txt 中的失败用例，执行 _compare_code_objects，
提取字节码差异类型，按区域类型 + 根因聚类。
输出 failures_root_causes.md。
"""
import os
import sys
import ast
import dis
import importlib.util
import inspect
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.code_generator import CodeGenerator

SKIP_OPS = {
    'RESUME', 'NOP', 'CACHE', 'JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE',
    'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
    'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE', 'FOR_ITER', 'SEND',
}


def filter_instrs(instrs):
    return [i for i in instrs if i.opname not in SKIP_OPS]


def diff_code_objects(orig, recomp, depth=0, path=""):
    """递归 diff，返回差异描述列表"""
    diffs = []
    if depth > 6:
        return diffs
    o = filter_instrs(list(dis.get_instructions(orig)))
    r = filter_instrs(list(dis.get_instructions(recomp)))
    if len(o) != len(r):
        diffs.append(f"{path}指令数: {len(o)} vs {len(r)}")
        # 额外记录前 10 条操作码对比
        for i in range(min(len(o), len(r), 10)):
            if o[i].opname != r[i].opname:
                diffs.append(f"{path}指令{i}: {o[i].opname} vs {r[i].opname}")
                break
        return diffs
    for i, (oi, ri) in enumerate(zip(o, r)):
        if oi.opname != ri.opname:
            diffs.append(f"{path}指令{i}操作码: {oi.opname} vs {ri.opname}")
            return diffs
        if oi.argval != ri.argval:
            if isinstance(oi.argval, type) and isinstance(ri.argval, type):
                sub = diff_code_objects(oi.argval, ri.argval, depth+1, f"{path}指令{i}嵌套:")
                diffs.extend(sub)
                if sub:
                    return diffs
            elif oi.opname not in ('LOAD_CONST',):
                try:
                    if abs(oi.argval or 0) != abs(ri.argval or 0):
                        diffs.append(f"{path}指令{i}参数: {oi.argval} vs {ri.argval}")
                        return diffs
                except TypeError:
                    diffs.append(f"{path}指令{i}参数: {oi.argval} vs {ri.argval}")
                    return diffs
    return diffs


def load_source_from_test(test_path: str) -> str:
    """从测试文件加载 SOURCE_CODE"""
    full = ROOT / test_path
    if not full.exists():
        return None
    try:
        with open(full, encoding='utf-8') as f:
            tree = ast.parse(f.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name) and t.id == 'SOURCE_CODE':
                        return ast.literal_eval(node.value)
    except Exception:
        return None
    return None


def decompile_source(src: str):
    """反编译，返回 (decompiled_str, error)"""
    try:
        code = compile(src, '<test>', 'exec')
        cfg = CFGBuilder().build(code)
        analyzer = RegionAnalyzer(cfg)
        generator = RegionASTGenerator(cfg, analyzer)
        result = generator.generate()
        decompiled = CodeGenerator().generate(result)
        return decompiled, None
    except Exception as e:
        return None, str(e)


def categorize_diff(diff_str: str) -> str:
    """将差异描述归类为根因类型"""
    if not diff_str:
        return "UNKNOWN"
    if "指令数" in diff_str and "vs" in diff_str:
        # 解析数字判断是多了还是少了
        import re
        m = re.search(r'(\d+) vs (\d+)', diff_str)
        if m:
            o, r = int(m.group(1)), int(m.group(2))
            if r > o:
                return "INSTR_OVERFLOW"  # 反编译多指令（多余代码）
            else:
                return "INSTR_UNDERFLOW"  # 反编译少指令（丢失代码）
    if "操作码" in diff_str:
        return "OPCODE_MISMATCH"
    if "参数" in diff_str:
        return "ARG_MISMATCH"
    return "OTHER"


def main():
    failures_file = ROOT / '.trae' / 'specs' / 'region-algorithm-deep-iteration' / 'baseline_failures.txt'
    # 解析失败用例
    test_cases = []  # [(category, test_path, error_msg)]
    current_cat = None
    current_dir = None
    with open(failures_file) as f:
        for line in f:
            line = line.strip()
            if line.startswith('# ['):
                # # [IF] tests/exhaustive/if_region (31 failed, 0 errors)
                parts = line.split('] ', 1)
                current_cat = parts[0][2:]
                current_dir = parts[1].split(' ')[0]
            elif line and not line.startswith('#'):
                # tests/exhaustive/if_region/test_xxx.py::Class::test - ErrorMsg
                if '::' in line:
                    test_path = line.split('::')[0]
                    error_msg = line.split(' - ', 1)[1] if ' - ' in line else ''
                    test_cases.append((current_cat, current_dir, test_path, error_msg))

    print(f"共 {len(test_cases)} 个失败用例待分析")

    # 按 test_path 去重（同一文件多个测试方法只分析一次）
    seen = set()
    unique_cases = []
    for cat, d, tp, em in test_cases:
        if tp not in seen:
            seen.add(tp)
            unique_cases.append((cat, d, tp, em))

    print(f"去重后 {len(unique_cases)} 个测试文件")

    # 对每个测试文件加载 SOURCE_CODE 并 diff
    results = []  # [(category, test_path, source, decompiled, diff, root_cause)]
    for cat, d, tp, em in unique_cases:
        src = load_source_from_test(tp)
        if src is None:
            results.append((cat, tp, None, None, "无法加载 SOURCE_CODE", "TEST_FRAMEWORK"))
            continue
        decompiled, err = decompile_source(src)
        if err:
            results.append((cat, tp, src, None, f"反编译异常: {err}", "DECOMPILE_ERROR"))
            continue
        try:
            recomp = compile(decompiled, '<dec>', 'exec')
        except SyntaxError as e:
            results.append((cat, tp, src, decompiled, f"语法错误: {e}", "SYNTAX_ERROR"))
            continue
        try:
            orig_code = compile(src, '<test>', 'exec')
            diffs = diff_code_objects(orig_code, recomp)
            if diffs:
                rc = categorize_diff(diffs[0])
                results.append((cat, tp, src, decompiled, "; ".join(diffs[:3]), rc))
            else:
                # 字节码等价但测试断言失败（结构断言过严）
                results.append((cat, tp, src, decompiled, "字节码等价但断言失败", "STRICT_ASSERT"))
        except Exception as e:
            results.append((cat, tp, src, decompiled, f"diff异常: {e}", "DIFF_ERROR"))

    # 按根因聚类
    by_cause = defaultdict(list)
    for cat, tp, src, dec, diff, rc in results:
        by_cause[rc].append((cat, tp, diff))

    # 输出报告
    out = ROOT / '.trae' / 'specs' / 'region-algorithm-deep-iteration' / 'failures_root_causes.md'
    with open(out, 'w', encoding='utf-8') as f:
        f.write("# 失败用例 → 区域类型 → 算法根因映射表\n\n")
        f.write(f"> 基线: 116 failed + 25 errors（去重后 {len(unique_cases)} 测试文件）\n")
        f.write(f"> 分析完成: {len(results)} 个\n\n")

        f.write("## 根因分类汇总\n\n")
        f.write("| 根因类型 | 数量 | 说明 |\n")
        f.write("|---------|------|------|\n")
        cause_desc = {
            "INSTR_OVERFLOW": "反编译多指令（生成多余代码）",
            "INSTR_UNDERFLOW": "反编译少指令（丢失代码/操作数）",
            "OPCODE_MISMATCH": "操作码不匹配（错误归约）",
            "ARG_MISMATCH": "参数不匹配（常量/变量名差异）",
            "STRICT_ASSERT": "字节码等价但测试结构断言过严",
            "SYNTAX_ERROR": "反编译结果语法错误",
            "DECOMPILE_ERROR": "反编译过程异常",
            "TEST_FRAMEWORK": "测试框架问题（无法加载源码/执行环境）",
            "DIFF_ERROR": "diff 分析异常",
        }
        for rc, items in sorted(by_cause.items(), key=lambda x: -len(x[1])):
            f.write(f"| {rc} | {len(items)} | {cause_desc.get(rc, '')} |\n")

        f.write("\n## 各根因详细用例\n\n")
        for rc, items in sorted(by_cause.items(), key=lambda x: -len(x[1])):
            f.write(f"### {rc}（{len(items)} 个）\n\n")
            for cat, tp, diff in items:
                f.write(f"- [{cat}] `{tp}`\n")
                f.write(f"  - diff: {diff[:200]}\n")
            f.write("\n")

    print(f"报告已保存: {out}")
    # 打印汇总
    print("\n根因汇总:")
    for rc, items in sorted(by_cause.items(), key=lambda x: -len(x[1])):
        print(f"  {rc}: {len(items)}")


if __name__ == '__main__':
    main()
