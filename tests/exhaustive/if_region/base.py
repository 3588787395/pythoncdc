import ast
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from tests.exhaustive.base import ExhaustiveTestCase


class IfRegionTestCase(ExhaustiveTestCase):
    REGION_TYPE = "IF_REGION"

    def verify_if_structure(self, expected_if_count: int = 1):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        if_nodes = self.find_all_nodes(tree, ast.If)
        self.assertEqual(
            len(if_nodes), expected_if_count,
            f"期望 {expected_if_count} 个If节点，实际找到 {len(if_nodes)} 个"
        )
        return if_nodes

    def verify_has_elif(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        for node in ast.walk(tree):
            if isinstance(node, ast.If) and node.orelse:
                for child in node.orelse:
                    if isinstance(child, ast.If):
                        return True
        return False

    def verify_has_else(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        for node in ast.walk(tree):
            if isinstance(node, ast.If) and node.orelse:
                for child in node.orelse:
                    if not isinstance(child, ast.If):
                        return True
        return False
