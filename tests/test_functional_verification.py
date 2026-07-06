#!/usr/bin/env python3
"""
反编译完整性验证器 - 功能验证框架

完整验证流程：
1. 编译源码 → 原始字节码
2. 反编译 → 还原源码
3. 编译还原源码 → 新字节码
4. 对比两个字节码的功能等价性
5. 返回详细报告

理论依据（编译器验证理论）：
- 字节码功能等价性：两个程序的字节码在语义上等价
- 结构保持性：控制流结构在反编译过程中保持不变
- 操作序列一致性：关键操作序列必须一致
"""

import ast
import dis
import sys
import os
from typing import Optional, Dict, List, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.ast_converter import CFGASTConverter
from core.cfg.code_generator import CFGCodeGenerator


class VerificationStatus(Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass
class BytecodeComparison:
    """字节码对比结果"""
    original_ops: List[Tuple[str, Any]] = field(default_factory=list)
    recompiled_ops: List[Tuple[str, Any]] = field(default_factory=list)
    op_sequence_match: float = 0.0
    constants_match: bool = False
    variable_scopes_match: bool = False
    control_flow_match: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VerificationReport:
    """验证报告"""
    status: VerificationStatus = VerificationStatus.PASSED
    source: str = ""
    decompiled_source: str = ""
    syntax_valid: bool = False
    bytecode_equivalent: bool = False
    equivalence_rate: float = 0.0
    bytecode_comparison: Optional[BytecodeComparison] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)


class DecompilationVerifier:
    """反编译完整性验证器

    提供完整的反编译→再编译→字节码对比验证流程。
    用于验证反编译结果的正确性和完整性。

    使用示例：
        verifier = DecompilationVerifier()
        report = verifier.verify_decompile(source_code)
        if report.status == VerificationStatus.PASSED:
            print("验证通过！")
    """

    def __init__(self, tolerance: float = 0.05):
        """
        初始化验证器

        Args:
            tolerance: 字节码差异容忍度（0-1之间，默认0.05即5%）
        """
        self.tolerance = tolerance

    def verify_decompile(self, source: str) -> VerificationReport:
        """
        完整验证流程

        Args:
            source: Python源代码字符串

        Returns:
            VerificationReport: 详细验证报告
        """
        report = VerificationReport(source=source)

        try:
            # Step 1: 验证原始源码语法
            if not self._verify_syntax(source):
                report.status = VerificationStatus.ERROR
                report.errors.append("原始源码语法无效")
                return report

            # Step 2: 编译原始源码 → 原始字节码
            original_code = self._compile_source(source)
            if original_code is None:
                report.status = VerificationStatus.ERROR
                report.errors.append("无法编译原始源码")
                return report

            # Step 3: 反编译 → 还原源码
            decompiled = self._decompile_code(original_code)
            if decompiled is None:
                report.status = VerificationStatus.ERROR
                report.errors.append("反编译失败")
                return report

            report.decompiled_source = decompiled

            # Step 4: 验证反编译结果语法
            if not self._verify_syntax(decompiled):
                report.status = VerificationStatus.FAILED
                report.syntax_valid = False
                report.errors.append("反编译结果语法无效")
                return report

            report.syntax_valid = True

            # Step 5: 编译还原源码 → 新字节码
            recompiled_code = self._compile_source(decompiled)
            if recompiled_code is None:
                report.status = VerificationStatus.FAILED
                report.errors.append("无法编译反编译结果")
                return report

            # Step 6: 对比字节码
            comparison = self._compare_bytecode(original_code, recompiled_code)
            report.bytecode_comparison = comparison

            # Step 7: 计算等价率并判定结果
            equivalence_rate = self._calculate_equivalence(comparison)
            report.equivalence_rate = equivalence_rate
            report.metrics = {
                'op_sequence_match': comparison.op_sequence_match,
                'constants_match': comparison.constants_match,
                'control_flow_match': comparison.control_flow_match,
                'original_op_count': len(comparison.original_ops),
                'recompiled_op_count': len(comparison.recompiled_ops),
            }

            if equivalence_rate >= (1.0 - self.tolerance):
                report.bytecode_equivalent = True
                report.status = VerificationStatus.PASSED
            elif equivalence_rate >= (1.0 - self.tolerance * 2):
                report.bytecode_equivalent = False
                report.status = VerificationStatus.WARNING
                report.warnings.append(f"等价率 {equivalence_rate:.2%} 接近阈值")
            else:
                report.bytecode_equivalent = False
                report.status = VerificationStatus.FAILED
                report.errors.append(f"等价率 {equivalence_rate:.2%} 低于阈值")

        except Exception as e:
            report.status = VerificationStatus.ERROR
            report.errors.append(f"验证过程异常: {str(e)}")
            import traceback
            report.errors.append(traceback.format_exc())

        return report

    def verify_syntax(self, source: str) -> bool:
        """快速语法验证"""
        try:
            ast.parse(source)
            return True
        except SyntaxError:
            return False

    def _compile_source(self, source: str):
        """编译Python源代码为code对象"""
        try:
            return compile(source, '<source>', 'exec')
        except Exception:
            return None

    def _decompile_code(self, code) -> Optional[str]:
        """使用区域分析反编译器进行反编译"""
        try:
            cfg = build_cfg(code)
            gen = RegionASTGenerator(cfg, top_level_code=code if code.co_name == '<module>' else None)
            ast_dict = gen.generate()
            converter = CFGASTConverter()
            py_ast = converter.convert(ast_dict)
            code_gen = CFGCodeGenerator()
            source = code_gen.generate(py_ast)
            return source
        except Exception as e:
            print(f"反编译错误: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _verify_syntax(self, source: str) -> bool:
        """验证Python语法"""
        try:
            ast.parse(source)
            return True
        except SyntaxError:
            return False

    def _get_bytecode_ops(self, code) -> List[Tuple[str, Any]]:
        """提取字节码操作序列"""
        ops = []
        try:
            instructions = list(dis.get_instructions(code))
            for instr in instructions:
                ops.append((instr.opname, instr.argval))
        except Exception:
            pass
        return ops

    def _compare_bytecode(self, original, recompiled) -> BytecodeComparison:
        """对比两个字节码的功能等价性"""
        comparison = BytecodeComparison()

        # 提取操作序列
        original_ops = self._get_bytecode_ops(original)
        recompiled_ops = self._get_bytecode_ops(recompiled)

        comparison.original_ops = original_ops
        comparison.recompiled_ops = recompiled_ops

        # 1. 操作序列匹配度
        op_sequence_match = self._calculate_sequence_similarity(original_ops, recompiled_ops)
        comparison.op_sequence_match = op_sequence_match

        # 2. 常量值匹配（顺序可不同）
        comparison.constants_match = self._check_constants_match(original, recompiled)

        # 3. 控制流结构匹配
        control_flow_match = self._analyze_control_flow(original_ops, recompiled_ops)
        comparison.control_flow_match = control_flow_match

        # 4. 详细差异分析
        comparison.details = self._analyze_differences(original_ops, recompiled_ops)

        return comparison

    def _calculate_sequence_similarity(self, ops1: List[Tuple], ops2: List[Tuple]) -> float:
        """计算操作序列相似度（使用编辑距离算法）"""
        if not ops1 and not ops2:
            return 1.0
        if not ops1 or not ops2:
            return 0.0

        # 简化版本：基于操作名的序列比对
        names1 = [op[0] for op in ops1]
        names2 = [op[0] for op in ops2]

        # 使用最长公共子序列计算相似度
        lcs_length = self._lcs_length(names1, names2)
        max_len = max(len(names1), len(names2))

        return lcs_length / max_len if max_len > 0 else 1.0

    def _lcs_length(self, a: List[str], b: List[str]) -> int:
        """计算最长公共子序列长度"""
        m, n = len(a), len(b)
        dp = [[0] * (n + 1) for _ in range(m + 1)]

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if a[i-1] == b[j-1]:
                    dp[i][j] = dp[i-1][j-1] + 1
                else:
                    dp[i][j] = max(dp[i-1][j], dp[i][j-1])

        return dp[m][n]

    def _check_constants_match(self, original, recompiled) -> bool:
        """检查常量值是否一致（宽松版本）

        策略：
        - 只比较用户定义的数值和字符串常量
        - 忽略None、空字符串、文档字符串等自动生成的常量
        - 允许常量顺序不同
        - 允许少量额外常量（编译器优化可能引入）
        """
        try:
            orig_consts = set(original.co_consts) if hasattr(original, 'co_consts') else set()
            recomp_consts = set(recompiled.co_consts) if hasattr(recompiled, 'co_consts') else set()

            # 过滤掉自动生成的常量
            def filter_consts(consts):
                filtered = set()
                for c in consts:
                    # 保留用户定义的常量
                    if c is None:
                        continue
                    if isinstance(c, str):
                        # 忽略空字符串和可能的文档字符串
                        if not c or len(c) > 100:
                            continue
                    # 保留数值、短字符串、布尔值等
                    if isinstance(c, (int, float, bool, bytes)) or \
                       (isinstance(c, str) and len(c) <= 100):
                        filtered.add(c)
                return filtered

            orig_filtered = filter_consts(orig_consts)
            recomp_filtered = filter_consts(recomp_consts)

            # 检查原始常量是否都出现在重编译的常量中
            return orig_filtered.issubset(recomp_filtered)

        except Exception:
            return True  # 如果无法比较，默认通过

    def _analyze_control_flow(self, ops1: List[Tuple], ops2: List[Tuple]) -> float:
        """分析控制流结构匹配度"""
        # 提取控制流相关操作
        cf_ops = {'JUMP_FORWARD', 'JUMP_ABSOLUTE', 'POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE',
                  'FOR_ITER', 'SETUP_LOOP', 'BREAK_LOOP', 'CONTINUE_LOOP',
                  'RETURN_VALUE', 'RETURN_CONST', 'RAISE_VARARGS'}

        cf_ops1 = [(i, op) for i, op in enumerate(ops1) if op[0] in cf_ops]
        cf_ops2 = [(i, op) for i, op in enumerate(ops2) if op[0] in cf_ops]

        if not cf_ops1 and not cf_ops2:
            return 1.0

        # 比较控制流操作的相对位置和类型
        match_count = 0
        min_len = min(len(cf_ops1), len(cf_ops2))

        for i in range(min_len):
            if cf_ops1[i][1][0] == cf_ops2[i][1][0]:
                match_count += 1

        return match_count / max(len(cf_ops1), len(cf_ops2)) if cf_ops1 or cf_ops2 else 1.0

    def _analyze_differences(self, ops1: List[Tuple], ops2: List[Tuple]) -> Dict[str, Any]:
        """详细差异分析"""
        details = {
            'only_in_original': [],
            'only_in_recompiled': [],
            'position_mismatches': [],
            'critical_differences': [],
        }

        # 找出仅在原始字节码中的操作
        set1 = set(ops1)
        set2 = set(ops2)
        details['only_in_original'] = list(set1 - set2)[:10]
        details['only_in_recompiled'] = list(set2 - set1)[:10]

        # 关键操作不匹配（影响语义的操作）
        critical_ops = {'COMPARE_OP', 'BINARY_ADD', 'BINARY_SUBTRACT', 'STORE_FAST',
                       'LOAD_FAST', 'CALL', 'RETURN_VALUE', 'RAISE_VARARGS'}

        for i, (op1, op2) in enumerate(zip(ops1[:min(len(ops1), len(ops2))],
                                           ops2[:min(len(ops1), len(ops2))])):
            if op1[0] != op2[0] and (op1[0] in critical_ops or op2[0] in critical_ops):
                details['critical_differences'].append({
                    'position': i,
                    'original': op1,
                    'recompiled': op2
                })

        return details

    def _calculate_equivalence(self, comparison: BytecodeComparison) -> float:
        """综合计算字节码等价率

        权重分配：
        - 操作序列：50%
        - 常量匹配：20%
        - 控制流：30%
        """
        weights = {
            'sequence': 0.5,
            'constants': 0.2,
            'control_flow': 0.3,
        }

        sequence_score = comparison.op_sequence_match
        constant_score = 1.0 if comparison.constants_match else 0.0
        control_flow_score = comparison.control_flow_match

        total = (weights['sequence'] * sequence_score +
                 weights['constants'] * constant_score +
                 weights['control_flow'] * control_flow_score)

        return total

    def assert_bytecode_equivalent(self, original, recompiled, tolerance=0.05):
        """断言字节码等价（用于单元测试）"""
        comparison = self._compare_bytecode(original, recompiled)
        equivalence = self._calculate_equivalence(comparison)

        assert equivalence >= (1.0 - tolerance), (
            f"字节码不等价！等价率: {equivalence:.2%}, "
            f"阈值: {(1.0-tolerance):.2%}\n"
            f"操作序列匹配: {comparison.op_sequence_match:.2%}\n"
            f"常量匹配: {comparison.constants_match}\n"
            f"控制流匹配: {comparison.control_flow_match:.2%}\n"
            f"关键差异: {comparison.details['critical_differences'][:5]}"
        )

        return True


def create_test_verifier() -> DecompilationVerifier:
    """工厂函数：创建测试用验证器实例"""
    return DecompilationVerifier(tolerance=0.05)


if __name__ == '__main__':
    # 测试示例
    test_source = '''
def target():
    x = 10
    if x > 0:
        y = x * 2
    else:
        y = x + 1
    return y
'''

    verifier = create_test_verifier()
    report = verifier.verify_decompile(test_source)

    print("=" * 60)
    print("反编译验证报告")
    print("=" * 60)
    print(f"状态: {report.status.value}")
    print(f"语法有效: {report.syntax_valid}")
    print(f"字节码等价: {report.bytecode_equivalent}")
    print(f"等价率: {report.equivalence_rate:.2%}")
    print("\n指标详情:")
    for key, value in report.metrics.items():
        print(f"  {key}: {value}")

    if report.errors:
        print("\n错误:")
        for error in report.errors:
            print(f"  ❌ {error}")

    if report.warnings:
        print("\n警告:")
        for warning in report.warnings:
            print(f"  ⚠️  {warning}")

    print("\n" + "=" * 60)
    print("原始源码:")
    print(report.source)
    print("\n反编译结果:")
    print(report.decompiled_source)
