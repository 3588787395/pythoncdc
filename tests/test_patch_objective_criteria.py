"""
客观补丁检测器 v2.0 单元测试

覆盖6维检测规则(D1-D6)，共15个测试用例：
  D1 算法依据性 x3 (有理论引用 / 无理论引用 / 模糊引用)
  D2 特殊分支数 x3 (0种分支 / 2种分支 / 5种分支)
  D3 后处理修正 x3 (修改已创建区域 / 不修改 / 读取后修改)
  D4 跨域访问   x3 (合法metadata访问 / 非法直接访问 / 边界间接访问)
  D5 多路径生成 x2 (单一入口 / 多入口)
  D6 硬编码引用 x1 (零硬编码 + 有硬编码)
"""

import ast
import sys
import textwrap
import pytest
import tempfile
import os
import importlib.util
from typing import Tuple

_spec = importlib.util.spec_from_file_location(
    "objective_patch_detector",
    os.path.join(os.path.dirname(__file__), "..", "core", "cfg", "objective_patch_detector.py")
)
_mod = importlib.util.module_from_spec(_spec)
sys.modules["objective_patch_detector"] = _mod
_spec.loader.exec_module(_mod)

ObjectivePatchDetector = _mod.ObjectivePatchDetector
PatchVerdict = _mod.PatchVerdict


detector = ObjectivePatchDetector()


def _make_method(source: str) -> Tuple[ast.FunctionDef, str]:
    """将源代码字符串解析为AST FunctionDef节点，返回(节点, 包装后源码)"""
    cleaned = textwrap.dedent(source)
    lines = cleaned.split('\n')
    indented = '\n'.join('    ' + line if line.strip() else '' for line in lines)
    wrapper = 'class FakeClass:\n' + indented
    tree = ast.parse(wrapper)
    cls = tree.body[0]
    return cls.body[0], wrapper


def _analyze_source(source: str) -> PatchVerdict:
    """分析单个方法源码，返回判定结果"""
    method_node, wrapped_source = _make_method(source)
    return detector.analyze_method(method_node, wrapped_source)


# ============================================================
# D1: 算法依据性检测 (3个用例)
# ============================================================


class TestD1AlgorithmBasis:
    """D1维度：算法依据性 — 检测文档字符串中的编译器理论引用"""

    def test_d1_with_theory_references(self):
        """D1合规：文档字符串包含多个编译器理论关键词"""
        source = textwrap.dedent('''
            def _handle_if_then_region(self, region):
                """
                IF_THEN区域协调器 - 基于支配树理论

                理论来源：
                - Dominator Tree (Aho et al., Dragon Book Ch.9)
                - Natural Loop Detection via back edges
                - Control Flow Graph structural analysis

                Args:
                    region: 待处理的区域对象
                Returns:
                    生成的AST节点
                """
                metadata = region.metadata
                return self._create_if_node(metadata)
        ''')
        verdict = _analyze_source(source)
        assert verdict.d1_score == 1.0, f"期望d1_score=1.0，实际={verdict.d1_score}，详情={verdict.violation_details}"
        assert not any("D1" in d for d in verdict.violation_details)

    def test_d1_without_theory_references(self):
        """D1违规：文档字符串中无任何编译器理论引用"""
        source = textwrap.dedent('''
            def _handle_if_then_region(self, region):
                """
                处理if-then区域

                这个方法负责处理if语句的区域。
                根据观察到的字节码模式来识别条件结构。
                """
                if region.type == 'IF':
                    pass
        ''')
        verdict = _analyze_source(source)
        assert verdict.d1_score == 0.0, f"期望d1_score=0.0，实际={verdict.d1_score}"
        assert any("D1违规" in d for d in verdict.violation_details)

    def test_d1_with_fuzzy_reference(self):
        """D1部分合规：仅包含1个理论关键词"""
        source = textwrap.dedent('''
            def _handle_for_loop_region(self, region):
                """
                处理for循环区域

                基于CFG分析方法实现循环识别。
                使用自然循环检测算法。
                """
                data = self._collect_loop_data(region)
                return self._create_loop_node(data)
        ''')
        verdict = _analyze_source(source)
        assert verdict.d1_score == 0.5, f"期望d1_score=0.5，实际={verdict.d1_score}"


# ============================================================
# D2: 特殊分支数检测 (3个用例)
# ============================================================


class TestD2SpecialBranches:
    """D2维度：特殊分支数 — 统计顶层if/elif分支模式数量"""

    def test_d2_zero_branches(self):
        """D2合规：方法内无条件分支(0种)"""
        source = textwrap.dedent('''
            def _collect_data(self, region):
                """收集区域数据"""
                result = {}
                result['blocks'] = list(region.blocks)
                result['metadata'] = dict(region.metadata)
                return result
        ''')
        verdict = _analyze_source(source)
        assert verdict.d2_score == 1.0, f"期望d2_score=1.0，实际={verdict.d2_score}"

    def test_d2_two_branches(self):
        """D2合规：恰好2种分支模式(≤2为合规)"""
        source = textwrap.dedent('''
            def _validate_data(self, data, metadata):
                """验证数据完整性"""
                if 'condition' not in data:
                    raise ValueError("missing condition")
                if data['condition'] is None:
                    raise ValueError("null condition")
                return True
        ''')
        verdict = _analyze_source(source)
        assert verdict.d2_score == 1.0, f"期望d2_score=1.0，实际={verdict.d2_score}"

    def test_d2_five_branches(self):
        """D2违规：超过3种不同分支模式"""
        source = textwrap.dedent('''
            def _complex_handler(self, node):
                """复杂处理器 - 针对多种特定模式"""
                if isinstance(node, ast.If):
                    return "if"
                elif isinstance(node, ast.For):
                    return "for"
                elif isinstance(node, ast.While):
                    return "while"
                elif isinstance(node, ast.Try):
                    return "try"
                elif isinstance(node, ast.With):
                    return "with"
                return "unknown"
        ''')
        verdict = _analyze_source(source)
        assert verdict.d2_score == 0.0, f"期望d2_score=0.0，实际={verdict.d2_score}"
        assert any("D2违规" in d for d in verdict.violation_details)


# ============================================================
# D3: 后处理修正检测 (3个用例)
# ============================================================


class TestD3Postprocessing:
    """D3维度：后处理修正 — 检测对已创建对象的修改操作"""

    def test_d3_modifies_created_region(self):
        """D3违规：在识别完成后修改已创建区域的属性"""
        source = textwrap.dedent('''
            def _fixup_regions(self, regions):
                """修复区域属性"""
                for region in regions:
                    if region.type == 'TRY':
                        region.try_blocks = [b for b in region.blocks if b.is_except]
                        region.except_handlers = []
                return regions
        ''')
        verdict = _analyze_source(source)
        assert verdict.d3_score == 0.0, f"期望d3_score=0.0，实际={verdict.d3_score}"
        assert any("D3违规" in d for d in verdict.violation_details)

    def test_d3_no_modification(self):
        """D3合规：只创建对象，不做后处理修改"""
        source = textwrap.dedent('''
            def _create_region(self, rtype, blocks, metadata):
                """创建新区域（纯构造）"""
                region = Region(type=rtype)
                region.set_blocks(blocks)
                region.set_metadata(metadata)
                return region
        ''')
        verdict = _analyze_source(source)
        assert verdict.d3_score == 1.0, f"期望d3_score=1.0，实际={verdict.d3_score}"

    def test_d3_read_then_modify(self):
        """D3违规：先读取再修改已创建对象"""
        source = textwrap.dedent('''
            def _adjust_region(self, region):
                """调整区域结构"""
                existing_blocks = region.blocks[:]
                region.blocks = [b for b in existing_blocks if b.is_valid]
                region.metadata['adjusted'] = True
                return region
        ''')
        verdict = _analyze_source(source)
        assert verdict.d3_score == 0.0, f"期望d3_score=0.0，实际={verdict.d3_score}"


# ============================================================
# D4: 跨域访问检测 (3个用例)
# ============================================================


class TestD4CrossDomainAccess:
    """D4维度：跨域访问 — 检测直接访问底层实现细节"""

    def test_d4_legal_metadata_access(self):
        """D4合规：通过Region.metadata获取数据"""
        source = textwrap.dedent('''
            def _get_condition(self, region):
                """通过metadata获取条件表达式"""
                cond_info = region.metadata.get('condition')
                if cond_info is None:
                    raise ValueError("Missing condition metadata")
                return cond_info['expr']
        ''')
        verdict = _analyze_source(source)
        assert verdict.d4_score == 1.0, f"期望d4_score=1.0，实际={verdict.d4_score}"

    def test_d4_illegal_direct_access(self):
        """D4违规：直接访问BasicBlock内部字段和指令列表"""
        source = textwrap.dedent('''
            def _scan_instructions(self, block):
                """直接扫描指令列表（跨域违规）"""
                results = []
                for instr in block.instructions:
                    if instr.opcode == 114:
                        results.append(('jump', instr.argval))
                    elif instr.opname == 'FOR_ITER':
                        results.append(('loop', instr.arg))
                return results
        ''')
        verdict = _analyze_source(source)
        assert verdict.d4_score == 0.0, f"期望d4_score=0.0，实际={verdict.d4_score}"
        assert any("D4违规" in d for d in verdict.violation_details)

    def test_d4_indirect_access_boundary(self):
        """D4边界：通过parent/children间接访问（应合规）"""
        source = textwrap.dedent('''
            def _traverse_children(self, region):
                """遍历子区域（通过公共API）"""
                children = region.children
                parent = region.parent
                blocks = region.blocks
                all_blocks = list(blocks)
                for child in children:
                    all_blocks.extend(child.blocks)
                return all_blocks
        ''')
        verdict = _analyze_source(source)
        assert verdict.d4_score == 1.0, f"期望d4_score=1.0，实际={verdict.d4_score}"


# ============================================================
# D5: 多路径生成检测 (2个用例)
# ============================================================


class TestD5MultiPathGeneration:
    """D5维度：多路径生成 — 同一区域类型的多个公开生成入口"""

    def test_d5_single_entry_point(self):
        """D5合规：每种区域类型只有一个生成入口"""
        source = textwrap.dedent('''
            def _handle_if_then_region(self, region):
                """IF_THEN区域唯一协调器"""
                data = self._collect_if_data(region)
                validated = self._validate_if_data(data)
                return self._create_if_node(validated)
        ''')
        all_methods = ['_handle_if_then_region', '_handle_if_else_region',
                       '_handle_for_loop_region', '_collect_if_data',
                       '_validate_if_data', '_create_if_node']
        method_node, wrapped = _make_method(source)
        verdict = detector.analyze_method(method_node, wrapped,
                                          all_methods=all_methods)
        assert verdict.d5_score == 1.0, f"期望d5_score=1.0，实际={verdict.d5_score}"

    def test_d5_multiple_entry_points(self):
        """D5违规：同一区域类型存在多个生成入口"""
        source = textwrap.dedent('''
            def _generate_if_then(self, cfg, entry_block):
                """备用if-then生成入口"""
                region = Region(type='IF_THEN')
                region.entry = entry_block
                return region
        ''')
        all_methods = ['_generate_if_then', '_handle_if_then_region',
                       '_generate_if_else', '_handle_if_else_region',
                       '_collect_data']
        method_node, wrapped = _make_method(source)
        verdict = detector.analyze_method(method_node, wrapped,
                                          all_methods=all_methods)
        assert verdict.d5_score == 0.0, f"期望d5_score=0.0，实际={verdict.d5_score}"
        assert any("D5违规" in d for d in verdict.violation_details)


# ============================================================
# D6: 硬编码引用检测 (1个综合用例)
# ============================================================


class TestD6HardcodedReferences:
    """D6维度：硬编码操作码字符串检测"""

    def test_d6_no_hardcoding(self):
        """D6合规：使用FeatureDetector而非硬编码操作码名称"""
        source = textwrap.dedent('''
            def _detect_jump_type(self, instr, detector):
                """使用特征检测器判断跳转类型"""
                if detector.is_conditional_jump(instr):
                    return 'conditional'
                if detector.is_unconditional_jump(instr):
                    return 'unconditional'
                if detector.is_loop_header(instr):
                    return 'loop'
                return 'other'
        ''')
        verdict = _analyze_source(source)
        assert verdict.d6_score == 1.0, f"期望d6_score=1.0，实际={verdict.d6_score}"

    def test_d6_has_hardcoding(self):
        """D6违规：直接使用硬编码的操作码名称字符串"""
        source = textwrap.dedent('''
            def _categorize_instruction(self, instr):
                """硬编码操作码分类"""
                opname = instr.opname
                if opname == 'POP_JUMP_IF_FALSE':
                    return 'cond_forward'
                elif opname == 'POP_JUMP_IF_TRUE':
                    return 'cond_true'
                elif opname == 'JUMP_ABSOLUTE':
                    return 'uncond_abs'
                elif opname == 'FOR_ITER':
                    return 'loop_iter'
                elif opname == 'COMPARE_OP':
                    return 'compare'
                return 'other'
        ''')
        verdict = _analyze_source(source)
        assert verdict.d6_score == 0.0, f"期望d6_score=0.0，实际={verdict.d6_score}"
        assert any("D6违规" in d for d in verdict.violation_details)


# ============================================================
# 综合测试：完整补丁判定与报告生成
# ============================================================


class TestIntegratedVerdict:
    """综合测试：≥3项违规即判定为补丁方法"""

    def test_clean_method_not_patch(self):
        """合规方法：所有维度均通过，不应被判定为补丁"""
        source = textwrap.dedent('''
            def _handle_if_then_region(self, region):
                """
                IF_THEN区域协调器

                基于支配树理论(Aho et al., Dragon Book Ch.9)和
                控制流图(CFG)的结构化分析方法。

                Args:
                    region: IF_THEN区域对象
                Returns:
                    AST If节点
                """
                metadata = region.metadata
                cond = metadata.get('condition')
                if cond is None:
                    raise ValueError("Missing condition")
                body = metadata.get('body_blocks')
                return self._build_if_node(cond, body)
        ''')
        verdict = _analyze_source(source)
        assert verdict.is_patch is False, f"合规方法不应被判定为补丁，violation_count={verdict.violation_count}"
        assert verdict.violation_count < 3

    def test_patch_method_detected(self):
        """补丁方法：≥3项违规应被正确判定"""
        source = textwrap.dedent('''
            def _patchy_handler(self, region):
                """处理各种特殊情况"""
                results = []
                for instr in region.instructions:
                    if instr.opname == 'POP_JUMP_IF_FALSE':
                        results.append('if_false')
                    elif instr.opname == 'FOR_ITER':
                        results.append('for_loop')
                    elif instr.opname == 'JUMP_ABSOLUTE':
                        results.append('jump_abs')
                    elif instr.opname == 'COMPARE_OP':
                        results.append('compare')
                    elif instr.opname == 'RETURN_VALUE':
                        results.append('return')
                region.patched = True
                region.extra_data = results
                return results
        ''')
        verdict = _analyze_source(source)
        assert verdict.is_patch is True, f"补丁方法应被判定为补丁，violation_count={verdict.violation_count}"
        assert verdict.violation_count >= 3

    def test_report_generation(self):
        """报告生成：验证结构化输出格式"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py',
                                          delete=False, encoding='utf-8') as f:
            f.write(textwrap.dedent('''
                class Analyzer:
                    def clean_method(self, region):
                        """
                        基于支配树理论和CFG分析的清洁方法。
                        """
                        return region.metadata.get('data')

                    def patchy_method(self, region):
                        """补丁式方法"""
                        for instr in region.instructions:
                            if instr.opname == 'FOR_ITER':
                                pass
                            elif instr.opname == 'POP_JUMP_IF_FALSE':
                                pass
                            elif instr.opname == 'JUMP_ABSOLUTE':
                                pass
                            elif instr.opname == 'COMPARE_OP':
                                pass
                        region.fixed = True
                        return region
            '''))
            tmp_path = f.name
        try:
            verdicts = detector.analyze_file(tmp_path)
            report = detector.generate_report(verdicts)
            assert len(verdicts) == 2, f"期望2个方法，实际{len(verdicts)}"
            assert "客观补丁检测报告" in report
            assert "D1算法依据" in report or "D1" in report
            assert "补丁方法" in report or "合规方法" in report
            patch_count = sum(1 for v in verdicts if v.is_patch)
            assert patch_count >= 1, f"至少应有1个补丁方法，实际{patch_count}"
        finally:
            os.unlink(tmp_path)

    def test_verdict_to_dict_serialization(self):
        """序列化：PatchVerdict.to_dict()输出完整性"""
        source = textwrap.dedent('''
            def sample_method(self, x):
                """基于SSA形式的变量重命名(Cytron et al.)"""
                return x + 1
        ''')
        verdict = _analyze_source(source)
        d = verdict.to_dict()
        assert 'method_name' in d
        assert 'is_patch' in d
        assert 'violation_count' in d
        assert 'violation_details' in d
        assert 'd1_score' in d
        assert 'd2_score' in d
        assert 'd3_score' in d
        assert 'd4_score' in d
        assert 'd5_score' in d
        assert 'd6_score' in d


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
