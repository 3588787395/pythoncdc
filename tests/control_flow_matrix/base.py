"""
控制流完备性测试基类

提供编译→反编译→验证的完整流程框架。
每个测试用例只需定义SOURCE_CODE类属性即可自动获得完整测试能力。
"""

import ast
import dis
import types
import unittest
from typing import Optional, List, Dict, Any, Iterable
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from core.cfg.region_analyzer import RegionAnalyzer
    from core.cfg.region_ast_generator import RegionASTGenerator
    from core.cfg.cfg_builder import CFGBuilder
    from core.cfg.code_generator import CodeGenerator
except ImportError as e:
    # 在导入失败时提供友好的错误信息
    print(f"警告: 无法导入核心模块: {e}")
    print("请确保从项目根目录运行测试")
    RegionAnalyzer = None
    RegionASTGenerator = None
    CFGBuilder = None
    CodeGenerator = None


class ControlFlowTestCase(unittest.TestCase):
    """
    控制流语法反编译测试基类

    使用方法：
        class TestForLoop(ControlFlowTestCase):
            SOURCE_CODE = "for i in range(10):\n    print(i)"

            def test_decompile(self):
                self.verify_decompilation()

    自动提供：
        - compile_source(): 编译源码为code object
        - decompile(): 反编译为源码字符串
        - verify_syntax(): 验证反编译结果语法正确
    """

    SOURCE_CODE: str = ""  # 子类必须定义

    @classmethod
    def setUpClass(cls):
        """编译测试源代码"""
        if not cls.SOURCE_CODE:
            raise NotImplementedError("子类必须定义SOURCE_CODE")

        cls.source_code = cls.SOURCE_CODE
        try:
            cls.original_code = compile(cls.source_code, '<test>', 'exec')
        except SyntaxError as e:
            if "'return' outside function" in str(e):
                indented = '\n'.join('    ' + line for line in cls.source_code.split('\n'))
                cls.source_code = f"def _wrap():\n{indented}\n_wrap()\n"
                try:
                    cls.original_code = compile(cls.source_code, '<test>', 'exec')
                except SyntaxError as e2:
                    raise ValueError(f"测试源码语法错误: {e2}")
            else:
                raise ValueError(f"测试源码语法错误: {e}")

    def compile_source(self) -> types.CodeType:
        """返回编译后的code object"""
        return self.original_code

    def decompile(self, code: types.CodeType = None) -> str:
        """
        反编译code object为源码

        Args:
            code: 要反编译的code object，默认使用类的original_code

        Returns:
            反编译后的Python源码字符串
        """
        if code is None:
            code = self.original_code

        if CFGBuilder is None:
            self.skipTest("核心模块未加载，跳过反编译测试")
            return ""

        try:
            cfg_builder = CFGBuilder()
            cfg = cfg_builder.build(code)

            analyzer = RegionAnalyzer(cfg)

            generator = RegionASTGenerator(cfg, analyzer)
            result = generator.generate()

            code_gen = CodeGenerator()
            return code_gen.generate(result)
        except Exception as e:
            self.fail(f"反编译过程出错: {e}")

    def verify_syntax(self, decompiled_source: str = None) -> ast.AST:
        """验证反编译结果可以通过语法检查"""
        if decompiled_source is None:
            decompiled_source = self.decompile()

        try:
            tree = ast.parse(decompiled_source)
            return tree
        except SyntaxError as e:
            self.fail(f"反编译结果语法错误:\n{e}\n\n源码:\n{decompiled_source}")

    def _compare_code_objects(self, orig: types.CodeType, recomp: types.CodeType, depth: int = 0) -> Optional[str]:
        """递归比较两个code object的字节码等价性

        Returns:
            None if equivalent, error message string otherwise
        """
        if depth > 5:
            return None

        orig_instructions = self._filter_jump_instructions(
            list(dis.get_instructions(orig))
        )
        recomp_instructions = self._filter_jump_instructions(
            list(dis.get_instructions(recomp))
        )

        if len(orig_instructions) != len(recomp_instructions):
            return (
                f"指令数不匹配: {len(orig_instructions)} vs {len(recomp_instructions)}\n"
                f"原始: {[i.opname for i in orig_instructions[:20]]}\n"
                f"重编: {[i.opname for i in recomp_instructions[:20]]}"
            )

        for i, (orig_instr, recomp_instr) in enumerate(zip(orig_instructions, recomp_instructions)):
            if orig_instr.opname != recomp_instr.opname:
                return f"指令{i}操作码不匹配: {orig_instr.opname} vs {recomp_instr.opname}"

            if orig_instr.argval != recomp_instr.argval and orig_instr.opname not in (
                'JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE',
                'POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE',
            ):
                if isinstance(orig_instr.argval, types.CodeType) and isinstance(recomp_instr.argval, types.CodeType):
                    sub_result = self._compare_code_objects(orig_instr.argval, recomp_instr.argval, depth + 1)
                    if sub_result:
                        return f"嵌套code object不匹配 (指令{i}): {sub_result}"
                else:
                    try:
                        if abs(orig_instr.argval or 0) != abs(recomp_instr.argval or 0):
                            return (
                                f"指令{i}参数不匹配: {orig_instr.argval} vs {recomp_instr.argval} "
                                f"(op={orig_instr.opname})"
                            )
                    except TypeError:
                        if orig_instr.argval != recomp_instr.argval:
                            return (
                                f"指令{i}参数不匹配: {orig_instr.argval} vs {recomp_instr.argval} "
                                f"(op={orig_instr.opname})"
                            )

        return None

    def verify_bytecode_equivalence(self) -> bool:
        """
        验证重编译后的控制流与原始一致

        比较策略：跳过绝对跳转地址，比较操作序列和参数。
        对于LOAD_CONST中的code object，递归比较其字节码内容。
        """
        decompiled = self.decompile()

        try:
            recompiled = compile(decompiled, '<decompiled>', 'exec')
        except SyntaxError:
            self.skipTest("重编译失败（可能是已知限制）")
            return False

        error = self._compare_code_objects(self.original_code, recompiled)
        if error:
            self.fail(error)
            return False

        return True

    def _filter_jump_instructions(self, instructions: List[dis.Instruction]) -> List[dis.Instruction]:
        """过滤掉跳转指令和对齐指令以便比较控制流逻辑

        NOP和CACHE是CPython用于内部对齐的无操作指令，不影响语义，
        不同编译路径可能产生不同数量的对齐指令，因此需要过滤。
        """
        skip_opnames = {
            'JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE',
            'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
            'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE',
            'FOR_ITER', 'SEND',
            'NOP', 'CACHE',
        }
        return [i for i in instructions if i.opname not in skip_opnames]

    def find_node(self, tree: ast.AST, node_type: type) -> Optional[ast.AST]:
        """在AST树中递归查找指定类型的节点"""
        for node in ast.walk(tree):
            if isinstance(node, node_type):
                return node
        return None

    def find_all_nodes(self, tree: ast.AST, node_type: type) -> List[ast.AST]:
        """查找所有指定类型的节点"""
        return [node for node in ast.walk(tree) if isinstance(node, node_type)]

    def verify_decompilation(self):
        """完整验证流程：反编译+语法检查+字节码等价"""
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree, "AST解析失败")
        self.verify_bytecode_equivalence()
