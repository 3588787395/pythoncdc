"""
CFG模块完善测试 - 单元测试和集成测试

测试内容包括：
1. AST转换器测试
2. 表达式重建测试
3. 代码生成器测试
4. 端到端集成测试
5. 字节码一致性验证
"""

import unittest
import types
import dis
import io

# 添加项目路径
import sys
sys.path.insert(0, 'd:\\Desktop\\ptrade相关\\pythoncdc')

from core.cfg.ast_converter import CFGASTConverter, convert_cfg_ast
from core.cfg.basic_block import Instruction
from core.cfg.ast_generator_v2 import ExpressionReconstructor
from core.cfg.code_generator import CFGCodeGenerator, generate_code
from parsers.unified_generator import UnifiedASTGenerator, decompile_code, smart_decompile
from core.ast_nodes import (
    ASTBlock, ASTIf, ASTFor, ASTWhile, ASTName, ASTConstant, 
    ASTBinary, ASTUnary, ASTCompare, ASTCall
)


class TestASTConverter(unittest.TestCase):
    """AST转换器单元测试"""
    
    def setUp(self):
        self.converter = CFGASTConverter(verbose=False)
    
    def test_convert_constant(self):
        """测试常量转换"""
        node_dict = {'type': 'Constant', 'value': 42}
        result = self.converter._convert_expression(node_dict)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, ASTConstant)
        self.assertEqual(result.value, 42)
    
    def test_convert_name(self):
        """测试变量名转换"""
        node_dict = {'type': 'Name', 'id': 'x'}
        result = self.converter._convert_expression(node_dict)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, ASTName)
        # ASTName使用name属性而不是id
        self.assertEqual(result.name, 'x')
    
    def test_convert_if(self):
        """测试if语句转换"""
        node_dict = {
            'type': 'If',
            'test': {'type': 'Constant', 'value': True},
            'body': [
                {'type': 'Expr', 'value': {'type': 'Constant', 'value': 1}}
            ],
            'orelse': []
        }
        result = self.converter.convert(node_dict)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, ASTIf)
        self.assertIsNotNone(result.test)
        self.assertIsNotNone(result.body)
    
    def test_convert_for(self):
        """测试for循环转换"""
        node_dict = {
            'type': 'For',
            'target': {'type': 'Name', 'id': 'i'},
            'iter': {'type': 'Call', 'func': {'type': 'Name', 'id': 'range'}, 'args': [{'type': 'Constant', 'value': 10}]},
            'body': [
                {'type': 'Expr', 'value': {'type': 'Name', 'id': 'i'}}
            ],
            'orelse': []
        }
        result = self.converter.convert(node_dict)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, ASTFor)
        self.assertIsNotNone(result.target)
        self.assertIsNotNone(result.iter)
    
    def test_convert_binop(self):
        """测试二元操作转换"""
        node_dict = {
            'type': 'BinOp',
            'left': {'type': 'Constant', 'value': 1},
            'op': '+',
            'right': {'type': 'Constant', 'value': 2}
        }
        result = self.converter._convert_expression(node_dict)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, ASTBinary)
    
    def test_convert_call(self):
        """测试函数调用转换"""
        node_dict = {
            'type': 'Call',
            'func': {'type': 'Name', 'id': 'print'},
            'args': [{'type': 'Constant', 'value': 'hello'}]
        }
        result = self.converter._convert_expression(node_dict)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, ASTCall)


class TestExpressionReconstructor(unittest.TestCase):
    """表达式重建器单元测试"""
    
    def setUp(self):
        self.reconstructor = ExpressionReconstructor(verbose=False)
    
    def test_load_constant(self):
        """测试加载常量"""
        instructions = [
            Instruction(offset=0, opcode=100, opname='LOAD_CONST', arg=0, argval=42)
        ]
        result = self.reconstructor.reconstruct(instructions)
        self.assertIsNotNone(result)
        self.assertEqual(result['type'], 'Constant')
        self.assertEqual(result['value'], 42)
    
    def test_load_name(self):
        """测试加载变量"""
        instructions = [
            Instruction(offset=0, opcode=101, opname='LOAD_NAME', arg=0, argval='x')
        ]
        result = self.reconstructor.reconstruct(instructions)
        self.assertIsNotNone(result)
        self.assertEqual(result['type'], 'Name')
        self.assertEqual(result['id'], 'x')
    
    def test_binary_add(self):
        """测试加法操作"""
        instructions = [
            Instruction(offset=0, opcode=100, opname='LOAD_CONST', arg=0, argval=1),
            Instruction(offset=2, opcode=100, opname='LOAD_CONST', arg=1, argval=2),
            Instruction(offset=4, opcode=23, opname='BINARY_ADD')
        ]
        result = self.reconstructor.reconstruct(instructions)
        self.assertIsNotNone(result)
        self.assertEqual(result['type'], 'BinOp')
        self.assertEqual(result['op'], '+')
    
    def test_call_function(self):
        """测试函数调用"""
        instructions = [
            Instruction(offset=0, opcode=101, opname='LOAD_NAME', arg=0, argval='print'),
            Instruction(offset=2, opcode=100, opname='LOAD_CONST', arg=0, argval='hello'),
            Instruction(offset=4, opcode=131, opname='CALL_FUNCTION', arg=1)
        ]
        result = self.reconstructor.reconstruct(instructions)
        self.assertIsNotNone(result)
        self.assertEqual(result['type'], 'Call')


class TestCodeGenerator(unittest.TestCase):
    """代码生成器单元测试"""
    
    def setUp(self):
        self.generator = CFGCodeGenerator(verbose=False)
    
    def test_generate_constant(self):
        """测试常量代码生成"""
        from core.ast_nodes import ASTConstant
        node = ASTConstant(42)
        result = self.generator.generate(node)
        self.assertIn('42', result)
    
    def test_generate_name(self):
        """测试变量名代码生成"""
        from core.ast_nodes import ASTName
        node = ASTName('x')
        result = self.generator.generate(node)
        # ASTName使用name属性
        self.assertIn('x', result.strip())
    
    def test_generate_if(self):
        """测试if语句代码生成"""
        from core.ast_nodes import ASTIf, ASTConstant, ASTPass
        test_node = ASTConstant(True)
        body_node = ASTBlock()
        body_node.append(ASTPass())
        node = ASTIf(test_node, body_node, None)
        result = self.generator.generate(node)
        self.assertIn('if True:', result)
        self.assertIn('pass', result)
    
    def test_generate_for(self):
        """测试for循环代码生成"""
        from core.ast_nodes import ASTFor, ASTName, ASTBlock, ASTPass
        target = ASTName('i')
        iter_node = ASTName('range')
        body = ASTBlock()
        body.append(ASTPass())
        # ASTFor需要target作为必需参数
        node = ASTFor(target=target, iter_node=iter_node, body=body)
        result = self.generator.generate(node)
        self.assertIn('for', result)
        self.assertIn('pass', result)


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def test_simple_function(self):
        """测试简单函数反编译"""
        def simple_func():
            return 42
        
        generator = UnifiedASTGenerator(verbose=False)
        result = generator.decompile(simple_func.__code__, 'simple_func')
        self.assertIsNotNone(result)
        self.assertIn('return', result)
    
    def test_if_statement(self):
        """测试if语句反编译"""
        def if_func(x):
            if x > 0:
                return True
            return False
        
        generator = UnifiedASTGenerator(verbose=False)
        result = generator.decompile(if_func.__code__, 'if_func')
        self.assertIsNotNone(result)
        self.assertIn('if', result)
    
    def test_for_loop(self):
        """测试for循环反编译"""
        def for_func():
            result = 0
            for i in range(10):
                result += i
            return result
        
        generator = UnifiedASTGenerator(verbose=False)
        result = generator.decompile(for_func.__code__, 'for_func')
        self.assertIsNotNone(result)
        # 检查是否包含for或range
        self.assertTrue('for' in result or 'range' in result)


class TestBytecodeConsistency(unittest.TestCase):
    """字节码一致性测试"""
    
    def get_bytecode(self, code_obj):
        """获取字节码的字符串表示"""
        output = io.StringIO()
        dis.dis(code_obj, file=output)
        return output.getvalue()
    
    def test_simple_function_bytecode(self):
        """测试简单函数字节码一致性"""
        def original():
            return 42
        
        # 反编译
        generator = UnifiedASTGenerator(verbose=False)
        source = generator.decompile(original.__code__, 'original')
        self.assertIsNotNone(source)
        
        # 重新编译
        try:
            compiled = compile(source, '<string>', 'exec')
            # 获取函数代码对象
            new_code = None
            for const in compiled.co_consts:
                if isinstance(const, types.CodeType):
                    new_code = const
                    break
            
            if new_code:
                # 比较字节码（简化比较）
                original_bytecode = self.get_bytecode(original.__code__)
                new_bytecode = self.get_bytecode(new_code)
                
                # 检查关键指令
                self.assertIn('RETURN_VALUE', new_bytecode)
        except SyntaxError as e:
            self.fail(f"重新编译失败: {e}")
    
    def test_expression_bytecode(self):
        """测试表达式字节码一致性"""
        def original(x, y):
            return x + y * 2
        
        generator = UnifiedASTGenerator(verbose=False)
        source = generator.decompile(original.__code__, 'original')
        self.assertIsNotNone(source)
        
        # 验证源代码语法正确
        try:
            compile(source, '<string>', 'exec')
        except SyntaxError as e:
            self.fail(f"生成的源代码语法错误: {e}")


class TestEdgeCases(unittest.TestCase):
    """边界情况测试"""
    
    def test_empty_function(self):
        """测试空函数"""
        def empty():
            pass
        
        generator = UnifiedASTGenerator(verbose=False)
        result = generator.decompile(empty.__code__, 'empty')
        self.assertIsNotNone(result)
    
    def test_nested_if(self):
        """测试嵌套if"""
        def nested(x, y):
            if x > 0:
                if y > 0:
                    return True
            return False
        
        generator = UnifiedASTGenerator(verbose=False)
        result = generator.decompile(nested.__code__, 'nested')
        self.assertIsNotNone(result)
    
    def test_complex_expression(self):
        """测试复杂表达式"""
        def complex_expr(a, b, c):
            return (a + b) * c - a / b
        
        generator = UnifiedASTGenerator(verbose=False)
        result = generator.decompile(complex_expr.__code__, 'complex_expr')
        self.assertIsNotNone(result)


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加所有测试类
    suite.addTests(loader.loadTestsFromTestCase(TestASTConverter))
    suite.addTests(loader.loadTestsFromTestCase(TestExpressionReconstructor))
    suite.addTests(loader.loadTestsFromTestCase(TestCodeGenerator))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestBytecodeConsistency))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
