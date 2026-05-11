"""
测试工具模块 - 为nook测试提供基础测试类
"""
import unittest
import sys
import os
from pathlib import Path
from typing import List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from core.cfg import build_cfg, generate_ast


class DecompileTestCase:
    """
    反编译测试用例类
    提供源代码编译、反编译和验证功能
    """
    
    def __init__(self, name: str, source_code: str, expected_patterns: List[str] = None):
        self.name = name
        self.source_code = source_code
        self.expected_patterns = expected_patterns or []
        self._result = None
        self._decompiled = None
    
    def build_cfg(self):
        """构建CFG"""
        code_obj = compile(self.source_code, '<string>', 'exec')
        return build_cfg(code_obj)
    
    def decompile(self) -> Optional[str]:
        """执行反编译"""
        try:
            cfg = self.build_cfg()
            ast_dict = generate_ast(cfg)
            self._result = ast_dict
            return ast_dict.get('type', 'Unknown')
        except Exception as e:
            print(f"反编译失败: {e}")
            return None
    
    def run(self) -> bool:
        """运行测试"""
        result_type = self.decompile()
        
        if not result_type:
            return False
        
        # 基本验证：检查是否生成了AST
        if result_type != 'Module':
            return False
        
        # 检查期望的模式（如果有）
        if self.expected_patterns:
            ast_str = str(self._result)
            for pattern in self.expected_patterns:
                if pattern not in ast_str:
                    print(f"  缺少期望模式: {pattern}")
                    return False
        
        return True
    
    def get_report(self) -> str:
        """生成测试报告"""
        status = "✓ PASS" if self._result else "✗ FAIL"
        lines = [
            f"测试: {self.name}",
            f"状态: {status}",
        ]
        
        if self._result:
            lines.append(f"AST类型: {self._result.get('type', 'N/A')}")
        
        return '\n'.join(lines)


def disassemble_code(source_code: str, name: str = "<module>"):
    """反汇编代码并打印字节码"""
    import dis
    
    print(f"\n{'=' * 60}")
    print(f"字节码: {name}")
    print('=' * 60)
    
    try:
        code_obj = compile(source_code, '<string>', 'exec')
        dis.dis(code_obj)
    except Exception as e:
        print(f"反汇编失败: {e}")


def build_cfg_from_source(source: str, func_name: str = None):
    """从源代码构建CFG的辅助函数"""
    code_obj = compile(source, '<string>', 'exec')
    return build_cfg(code_obj)


class CFGTestBase(unittest.TestCase):
    """
    CFG测试基类
    提供通用的CFG构建和验证方法
    """
    
    def build_cfg_from_source(self, source: str, func_name: str = None):
        """从源代码构建CFG"""
        code_obj = compile(source, '<string>', 'exec')
        return build_cfg(code_obj)
    
    def assert_cfg_valid(self, cfg):
        """断言CFG有效"""
        self.assertIsNotNone(cfg)
        self.assertGreater(len(cfg.blocks), 0)
        self.assertIsNotNone(cfg.entry_block)
    
    def assert_ast_module(self, ast_dict):
        """断言AST是Module类型"""
        self.assertEqual(ast_dict.get('type'), 'Module')


__all__ = [
    'DecompileTestCase',
    'disassemble_code',
    'build_cfg_from_source',
    'CFGTestBase',
]
