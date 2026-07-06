"""
字节码对比工具 (CFG模式专用) - 用于比较原始PYC和CFG反编译后的字节码差异
"""

import dis
import marshal
import types
import tempfile
import os
import sys
from typing import List, Tuple, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pycdc import PycDecompiler


class DiffType(Enum):
    """差异类型"""
    CONST_POOL_MISMATCH = "常量池不匹配"
    INSTRUCTION_COUNT = "指令数量不同"
    OPCODE_MISMATCH = "操作码不匹配"
    ARG_MISMATCH = "参数不匹配"
    MISSING_INSTRUCTION = "指令缺失"
    EXTRA_INSTRUCTION = "额外指令"
    CONTROL_FLOW = "控制流差异"
    IMPORT_STATEMENT = "导入语句差异"
    CLASS_DEFINITION = "类定义差异"
    EXCEPTION_HANDLING = "异常处理差异"
    WITH_STATEMENT = "with语句差异"
    COMPREHENSION = "推导式差异"
    DECORATOR = "装饰器差异"
    TYPE_ANNOTATION = "类型注解差异"
    CHAINED_COMPARISON = "链式比较差异"


@dataclass
class BytecodeDiff:
    """字节码差异详情"""
    func_name: str
    diff_type: DiffType
    position: int
    offset: int
    orig: str
    new: str
    description: str = ""
    suggestion: str = ""


@dataclass
class FunctionAnalysis:
    """函数分析结果"""
    func_name: str
    orig_instr_count: int
    new_instr_count: int
    match: bool
    diffs: List[BytecodeDiff] = field(default_factory=list)
    consts_diff: List[Tuple[Any, Any]] = field(default_factory=list)
    
    def add_diff(self, diff: BytecodeDiff):
        self.diffs.append(diff)
        self.match = False


@dataclass
class AnalysisReport:
    """完整分析报告"""
    pyc_path: str
    overall_match: bool
    total_functions: int
    matched_functions: int
    failed_functions: int
    function_analyses: List[FunctionAnalysis] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)
    
    def print_report(self, max_diffs_per_func: int = 5):
        """打印分析报告"""
        print(f"\n{'='*70}")
        print(f"PYC文件: {self.pyc_path}")
        print(f"总体结果: {'✅ 完全匹配' if self.overall_match else '❌ 存在差异'}")
        print(f"函数统计: 共{self.total_functions}个 | 匹配{self.matched_functions}个 | 失败{self.failed_functions}个")
        print(f"{'='*70}\n")
        
        if self.summary:
            print("差异类型统计:")
            for diff_type, count in sorted(self.summary.items(), key=lambda x: -x[1]):
                print(f"  - {diff_type}: {count}处")
            print()
        
        for fa in self.function_analyses:
            if not fa.match:
                print(f"函数: {fa.func_name}")
                print(f"  指令数: 原始{fa.orig_instr_count} vs 新生{fa.new_instr_count}")
                for i, diff in enumerate(fa.diffs[:max_diffs_per_func]):
                    print(f"  位置{diff.position}(偏移{diff.offset}): {diff.orig} != {diff.new}")
                    if diff.description:
                        print(f"    说明: {diff.description}")
                    if diff.suggestion:
                        print(f"    建议: {diff.suggestion}")
                if len(fa.diffs) > max_diffs_per_func:
                    print(f"  ... 还有 {len(fa.diffs) - max_diffs_per_func} 处差异")
                print()


def analyze_const_pool_diff(orig_code: types.CodeType, new_code: types.CodeType) -> List[Tuple[Any, Any]]:
    """分析常量池差异"""
    diffs = []
    orig_consts = orig_code.co_consts
    new_consts = new_code.co_consts
    
    max_len = max(len(orig_consts), len(new_consts))
    for i in range(max_len):
        o = orig_consts[i] if i < len(orig_consts) else None
        n = new_consts[i] if i < len(new_consts) else None
        
        if isinstance(o, types.CodeType) and isinstance(n, types.CodeType):
            # 嵌套代码对象，递归分析
            nested_diffs = analyze_const_pool_diff(o, n)
            diffs.extend([(f"[{i}].{k}", v) for k, v in nested_diffs])
        elif o != n:
            diffs.append((i, (o, n)))
    
    return diffs


def classify_diff(func_name: str, position: int, offset: int, 
                  orig_instr: dis.Instruction, new_instr: dis.Instruction) -> BytecodeDiff:
    """分类差异类型并提供修复建议"""
    
    orig_str = f"{orig_instr.opname}({orig_instr.arg})"
    new_str = f"{new_instr.opname}({new_instr.arg})"
    
    # 常量加载指令索引偏移
    if orig_instr.opname == 'LOAD_CONST' and new_instr.opname == 'LOAD_CONST':
        diff_type = DiffType.CONST_POOL_MISMATCH
        description = "常量池索引偏移"
        suggestion = "检查常量池顺序，确保与原始代码一致"
    
    # 导入语句相关
    elif orig_instr.opname in ('IMPORT_NAME', 'IMPORT_FROM', 'IMPORT_STAR') or \
         new_instr.opname in ('IMPORT_NAME', 'IMPORT_FROM', 'IMPORT_STAR'):
        diff_type = DiffType.IMPORT_STATEMENT
        description = "导入语句处理错误"
        suggestion = "检查IMPORT_NAME/IMPORT_FROM指令序列"
    
    # 类定义相关
    elif orig_instr.opname == 'LOAD_BUILD_CLASS' or new_instr.opname == 'LOAD_BUILD_CLASS':
        diff_type = DiffType.CLASS_DEFINITION
        description = "类定义字节码差异"
        suggestion = "检查LOAD_BUILD_CLASS和MAKE_FUNCTION序列"
    
    # 异常处理相关
    elif orig_instr.opname in ('PUSH_EXC_INFO', 'CHECK_EXC_MATCH', 'POP_EXCEPT', 'RERAISE') or \
         new_instr.opname in ('PUSH_EXC_INFO', 'CHECK_EXC_MATCH', 'POP_EXCEPT', 'RERAISE'):
        diff_type = DiffType.EXCEPTION_HANDLING
        description = "异常处理指令差异"
        suggestion = "检查try-except-finally字节码生成"
    
    # with语句相关
    elif orig_instr.opname in ('BEFORE_WITH', 'WITH_EXCEPT_START', 'SETUP_FINALLY') or \
         new_instr.opname in ('BEFORE_WITH', 'WITH_EXCEPT_START', 'SETUP_FINALLY'):
        diff_type = DiffType.WITH_STATEMENT
        description = "with语句字节码差异"
        suggestion = "检查上下文管理器指令序列"
    
    # 推导式相关
    elif orig_instr.opname in ('MAKE_CELL', 'LOAD_CLOSURE', 'STORE_DEREF', 'LIST_APPEND') or \
         new_instr.opname in ('MAKE_CELL', 'LOAD_CLOSURE', 'STORE_DEREF', 'LIST_APPEND'):
        diff_type = DiffType.COMPREHENSION
        description = "推导式字节码差异"
        suggestion = "检查推导式闭包和作用域处理"
    
    # 装饰器相关
    elif orig_instr.opname in ('LOAD_DEREF', 'STORE_DEREF') or \
         new_instr.opname in ('LOAD_DEREF', 'STORE_DEREF'):
        diff_type = DiffType.DECORATOR
        description = "装饰器/闭包变量差异"
        suggestion = "检查闭包变量索引"
    
    # 链式比较
    elif orig_instr.opname in ('JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP') or \
         new_instr.opname in ('JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP'):
        diff_type = DiffType.CHAINED_COMPARISON
        description = "链式比较字节码差异"
        suggestion = "检查链式比较(如0<x<100)的处理"
    
    # 控制流差异
    elif orig_instr.opname.startswith('JUMP') or new_instr.opname.startswith('JUMP'):
        diff_type = DiffType.CONTROL_FLOW
        description = "控制流指令差异"
        suggestion = "检查条件判断和跳转逻辑"
    
    # 操作码不匹配
    elif orig_instr.opcode != new_instr.opcode:
        diff_type = DiffType.OPCODE_MISMATCH
        description = "操作码类型不同"
        suggestion = f"检查{orig_instr.opname} vs {new_instr.opname}的处理"
    
    # 参数不匹配
    else:
        diff_type = DiffType.ARG_MISMATCH
        description = "指令参数不同"
        suggestion = "检查指令参数生成逻辑"
    
    return BytecodeDiff(
        func_name=func_name,
        diff_type=diff_type,
        position=position,
        offset=offset,
        orig=orig_str,
        new=new_str,
        description=description,
        suggestion=suggestion
    )


def analyze_function_bytecode(func_name: str, orig_code: types.CodeType, 
                               new_code: types.CodeType) -> FunctionAnalysis:
    """详细分析单个函数的字节码差异"""
    
    orig_ins = list(dis.get_instructions(orig_code))
    new_ins = list(dis.get_instructions(new_code))
    
    analysis = FunctionAnalysis(
        func_name=func_name,
        orig_instr_count=len(orig_ins),
        new_instr_count=len(new_ins),
        match=len(orig_ins) == len(new_ins)
    )
    
    # 分析常量池差异
    analysis.consts_diff = analyze_const_pool_diff(orig_code, new_code)
    
    # 导入编译器优化处理器
    try:
        from .compiler_optimization_handler import optimization_handler
    except ImportError:
        try:
            from compiler_optimization_handler import optimization_handler
        except ImportError:
            optimization_handler = None
    
    # 对比指令
    min_len = min(len(orig_ins), len(new_ins))
    for i in range(min_len):
        o, n = orig_ins[i], new_ins[i]
        if o.opcode != n.opcode or o.arg != n.arg:
            # 检查是否是编译器优化导致的差异
            if optimization_handler:
                is_opt_diff = optimization_handler.is_compiler_optimization_diff(
                    func_name, i, o, n, orig_code, new_code
                )
                if is_opt_diff:
                    # 标记为编译器优化差异，但不添加到diff列表
                    # 而是记录为预期的差异
                    continue
            
            diff = classify_diff(func_name, i, o.offset, o, n)
            analysis.add_diff(diff)
    
    # 处理长度差异
    if len(orig_ins) > len(new_ins):
        for i in range(len(new_ins), len(orig_ins)):
            diff = BytecodeDiff(
                func_name=func_name,
                diff_type=DiffType.MISSING_INSTRUCTION,
                position=i,
                offset=orig_ins[i].offset,
                orig=f"{orig_ins[i].opname}({orig_ins[i].arg})",
                new="<缺失>",
                description="新生代码缺失指令",
                suggestion="检查代码生成是否完整"
            )
            analysis.add_diff(diff)
    elif len(new_ins) > len(orig_ins):
        for i in range(len(orig_ins), len(new_ins)):
            diff = BytecodeDiff(
                func_name=func_name,
                diff_type=DiffType.EXTRA_INSTRUCTION,
                position=i,
                offset=new_ins[i].offset,
                orig="<缺失>",
                new=f"{new_ins[i].opname}({new_ins[i].arg})",
                description="新生代码有多余指令",
                suggestion="检查是否生成了冗余代码"
            )
            analysis.add_diff(diff)
    
    return analysis


def extract_functions(code_obj: types.CodeType, prefix: str = "") -> Dict[str, types.CodeType]:
    """递归提取代码对象中的所有函数"""
    functions = {}
    name = prefix + code_obj.co_name if prefix else code_obj.co_name
    functions[name] = code_obj
    
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType):
            nested_name = f"{name}.{const.co_name}" if name != "<module>" else const.co_name
            functions.update(extract_functions(const, f"{nested_name}." if nested_name != const.co_name else ""))
    
    return functions


def analyze_bytecode_detailed(orig_pyc_path: str, new_pyc_path: str) -> AnalysisReport:
    """详细分析两个字节码文件的差异"""
    
    # 加载原始代码
    with open(orig_pyc_path, 'rb') as f:
        f.read(16)
        orig_code = marshal.load(f)
    
    # 加载新生代码
    with open(new_pyc_path, 'rb') as f:
        f.read(16)
        new_code = marshal.load(f)
    
    orig_funcs = extract_functions(orig_code)
    new_funcs = extract_functions(new_code)
    
    report = AnalysisReport(
        pyc_path=orig_pyc_path,
        overall_match=True,
        total_functions=len(orig_funcs),
        matched_functions=0,
        failed_functions=0
    )
    
    all_func_names = set(orig_funcs.keys()) | set(new_funcs.keys())
    
    for name in sorted(all_func_names):
        if name not in orig_funcs:
            fa = FunctionAnalysis(
                func_name=name,
                orig_instr_count=0,
                new_instr_count=len(list(dis.get_instructions(new_funcs[name]))),
                match=False
            )
            fa.add_diff(BytecodeDiff(
                func_name=name,
                diff_type=DiffType.MISSING_INSTRUCTION,
                position=0,
                offset=0,
                orig="<函数不存在>",
                new="<存在>",
                description="函数在原始代码中不存在"
            ))
            report.function_analyses.append(fa)
            report.failed_functions += 1
        elif name not in new_funcs:
            fa = FunctionAnalysis(
                func_name=name,
                orig_instr_count=len(list(dis.get_instructions(orig_funcs[name]))),
                new_instr_count=0,
                match=False
            )
            fa.add_diff(BytecodeDiff(
                func_name=name,
                diff_type=DiffType.MISSING_INSTRUCTION,
                position=0,
                offset=0,
                orig="<存在>",
                new="<函数不存在>",
                description="函数在新生代码中不存在"
            ))
            report.function_analyses.append(fa)
            report.failed_functions += 1
        else:
            fa = analyze_function_bytecode(name, orig_funcs[name], new_funcs[name])
            report.function_analyses.append(fa)
            if fa.match:
                report.matched_functions += 1
            else:
                report.failed_functions += 1
                report.overall_match = False
    
    # 统计差异类型
    for fa in report.function_analyses:
        for diff in fa.diffs:
            diff_type_name = diff.diff_type.value
            report.summary[diff_type_name] = report.summary.get(diff_type_name, 0) + 1
    
    return report


def decompile_with_cfg(pyc_path: str) -> str:
    """使用纯CFG模式反编译PYC文件"""
    decompiler = PycDecompiler()
    if not decompiler.load_file(pyc_path):
        raise RuntimeError(f"无法加载PYC文件: {pyc_path}")
    
    import io
    output = io.StringIO()
    if not decompiler.decompile(output, use_cfg=True, cfg_hybrid=False):
        raise RuntimeError("CFG反编译失败")
    
    return output.getvalue()


def test_cfg_decompile_and_compare(pyc_path: str) -> AnalysisReport:
    """测试CFG反编译并生成详细分析报告"""
    # 使用CFG模式反编译
    source = decompile_with_cfg(pyc_path)
    
    # 检查语法
    try:
        compile(source, '<decompiled>', 'exec')
    except SyntaxError as e:
        report = AnalysisReport(
            pyc_path=pyc_path,
            overall_match=False,
            total_functions=0,
            matched_functions=0,
            failed_functions=1
        )
        fa = FunctionAnalysis(
            func_name="<module>",
            orig_instr_count=0,
            new_instr_count=0,
            match=False
        )
        fa.add_diff(BytecodeDiff(
            func_name="<module>",
            diff_type=DiffType.OPCODE_MISMATCH,
            position=0,
            offset=0,
            orig="<有效代码>",
            new="<语法错误>",
            description=f"语法错误: {e}"
        ))
        report.function_analyses.append(fa)
        return report
    
    # 重新编译并保存为PYC
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(source)
        temp_py = f.name
    
    try:
        import py_compile
        temp_pyc = temp_py + 'c'
        py_compile.compile(temp_py, temp_pyc, doraise=True)
        report = analyze_bytecode_detailed(pyc_path, temp_pyc)
        
        if os.path.exists(temp_pyc):
            os.remove(temp_pyc)
        
        return report
    finally:
        if os.path.exists(temp_py):
            os.remove(temp_py)


def compare_bytecode_detailed(orig_pyc_path: str, new_pyc_path: str) -> List[Tuple[str, str]]:
    """兼容旧接口的详细比较函数"""
    report = analyze_bytecode_detailed(orig_pyc_path, new_pyc_path)
    diffs = []
    for fa in report.function_analyses:
        for diff in fa.diffs:
            diffs.append((fa.func_name, f"位置{diff.position}: {diff.orig} != {diff.new}"))
    return diffs


def print_diff_report(diffs: List[Tuple[str, str]], max_display: int = 50):
    """兼容旧接口的打印函数"""
    if not diffs:
        print("✅ 字节码完全匹配！")
        return
    
    print(f"❌ 发现 {len(diffs)} 处差异:\n")
    
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


def analyze_pyc_with_cfg(pyc_path: str) -> Dict[str, Any]:
    """使用纯CFG模式分析PYC文件（兼容旧接口）"""
    result = {
        'success': False,
        'source': None,
        'error': None,
        'diffs': []
    }
    
    try:
        source = decompile_with_cfg(pyc_path)
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
        report = test_cfg_decompile_and_compare(pyc_path)
        result['report'] = report
        for fa in report.function_analyses:
            for diff in fa.diffs:
                result['diffs'].append((fa.func_name, f"位置{diff.position}: {diff.orig} != {diff.new}"))
    except Exception as e:
        result['error'] = f"异常: {e}"
        import traceback
        result['traceback'] = traceback.format_exc()
    
    return result


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python bytecode_comparator_cfg.py <pyc文件>")
        sys.exit(1)
    
    pyc_path = sys.argv[1]
    print(f"分析文件: {pyc_path}")
    print(f"模式: 纯CFG模式 (cfg_hybrid=False)")
    print("=" * 60)
    
    try:
        report = test_cfg_decompile_and_compare(pyc_path)
        report.print_report(max_diffs_per_func=10)
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()
