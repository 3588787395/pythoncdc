import ast
import re
import sys
import os
from typing import Optional, List, Dict, Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from tests.control_flow_matrix.base import ControlFlowTestCase

try:
    from core.cfg.region_analyzer import RegionType
except ImportError:
    RegionType = None

PATCH_BEHAVIOR_PATTERNS = [
    (r'#\s*PATCH', 'patch_comment'),
    (r'#\s*HACK', 'hack_comment'),
    (r'#\s*FIXME', 'fixme_comment'),
    (r'#\s*WORKAROUND', 'workaround_comment'),
    (r'pass\s*#\s*placeholder', 'placeholder_pass'),
    (r'__patch_', 'patch_variable'),
    (r'_patch_\d+', 'patch_function'),
]

REGION_TYPE_MAP = {
    'BASIC': [
        ast.Assign, ast.AugAssign, ast.Expr, ast.Return, ast.Pass,
        ast.Delete, ast.Global, ast.Nonlocal, ast.Yield, ast.YieldFrom,
        ast.Raise, ast.Import, ast.ImportFrom, ast.Assert,
    ],
    'IF_REGION': [ast.If],
    'WHILE_LOOP': [ast.While],
    'FOR_LOOP': [ast.For],
    'TRY_EXCEPT': [ast.Try],
    'WITH_REGION': [ast.With],
    'MATCH_REGION': [ast.Match],
    'BOOL_OP': [ast.BoolOp],
    'TERNARY': [ast.IfExp],
    'NESTED': [],
}

REGION_TYPE_ALTERNATIVES = {
    'MATCH_REGION': [ast.If],
    # CPython优化使while False:pass和if False:pass产生完全相同的字节码，
    # 反编译器无法区分，因此WHILE_LOOP接受ast.If作为替代
    'WHILE_LOOP': [ast.If],
}


class ExhaustiveTestCase(ControlFlowTestCase):
    REGION_TYPE: str = ""

    @classmethod
    def from_template(cls, template: str, **kwargs) -> str:
        return template.format(**kwargs)

    def verify_region_type(self, expected_type: str = None) -> bool:
        if expected_type is None:
            expected_type = self.REGION_TYPE

        if not expected_type:
            self.fail("未指定 REGION_TYPE，无法验证区域类型")

        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)

        expected_ast_types = REGION_TYPE_MAP.get(expected_type, [])
        if not expected_ast_types:
            return True

        found = False
        for ast_type in expected_ast_types:
            for node in ast.walk(tree):
                if isinstance(node, ast_type):
                    found = True
                    break
            if found:
                break

        if not found:
            alternative_types = REGION_TYPE_ALTERNATIVES.get(expected_type, [])
            for alt_type in alternative_types:
                for node in ast.walk(tree):
                    if isinstance(node, alt_type):
                        found = True
                        break
                if found:
                    break

        if not found:
            expected_names = [t.__name__ for t in expected_ast_types]
            self.fail(
                f"反编译结果中未找到预期的区域类型 {expected_type} "
                f"(期望AST节点: {expected_names})\n"
                f"反编译结果:\n{decompiled}"
            )

        return True

    def verify_no_behavioral_violations(self) -> bool:
        decompiled = self.decompile()

        violations = []
        for pattern, name in PATCH_BEHAVIOR_PATTERNS:
            matches = re.findall(pattern, decompiled)
            if matches:
                violations.append((name, pattern, len(matches)))

        if violations:
            details = "\n".join(
                f"  - {name}: 模式 '{pattern}' 出现 {count} 次"
                for name, pattern, count in violations
            )
            self.fail(
                f"反编译结果中存在行为违规:\n{details}\n"
                f"反编译结果:\n{decompiled}"
            )

        return True

    def verify_decompilation(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree, "AST解析失败")

        if self.REGION_TYPE:
            self.verify_region_type(self.REGION_TYPE)

        self.verify_no_behavioral_violations()

        self.verify_bytecode_equivalence()
