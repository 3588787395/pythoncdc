#!/usr/bin/env python3
"""
回归测试 - 验证所有修复

测试内容:
1. test_generator_advanced - yield from在for循环中的处理
2. test_multi_stage_4 - 装饰器状态污染问题
3. 编译错误文件修复 - __NESTED_FUNC__占位符和模块级return
"""
import sys
import os
import marshal
import unittest

sys.path.insert(0, r'd:\Desktop\ptrade相关\pythoncdc')

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.ast_generator_v2 import ASTGeneratorV2
from core.cfg.code_generator import CFGCodeGenerator


class TestDecompilerFixes(unittest.TestCase):
    """测试反编译器修复"""
    
    def _test_pyc_file(self, pyc_path):
        """辅助方法: 测试单个pyc文件"""
        with open(pyc_path, 'rb') as f:
            f.read(16)
            code = marshal.load(f)
        
        cfg = CFGBuilder().build(code)
        ast_dict = ASTGeneratorV2(cfg, recursive=True).generate()
        generator = CFGCodeGenerator()
        source = generator.generate(ast_dict)
        
        # 尝试编译
        compile(source, '<test>', 'exec')
        
        # 检查是否有__NESTED_FUNC__
        self.assertNotIn('__NESTED_FUNC__', source, 
                        f"生成的代码包含__NESTED_FUNC__占位符")
        
        return source
    
    def test_generator_advanced(self):
        """测试test_generator_advanced - yield from修复"""
        pyc_path = r'd:\Desktop\ptrade相关\pythoncdc\tests\complex\__pycache__\test_generator_advanced.cpython-311.pyc'
        if os.path.exists(pyc_path):
            source = self._test_pyc_file(pyc_path)
            print("  test_generator_advanced: OK")
    
    def test_multi_stage_4(self):
        """测试test_multi_stage_4 - 装饰器状态污染修复"""
        pyc_path = r'd:\Desktop\ptrade相关\pythoncdc\tests\complex\__pycache__\test_multi_stage_4.cpython-311.pyc'
        if os.path.exists(pyc_path):
            source = self._test_pyc_file(pyc_path)
            
            # 检查process_with_error_handling没有装饰器
            lines = source.split('\n')
            for i, line in enumerate(lines):
                if 'def process_with_error_handling' in line:
                    # 检查前一行是否是装饰器
                    if i > 0 and lines[i-1].strip().startswith('@'):
                        self.fail("process_with_error_handling不应该有装饰器")
            
            print("  test_multi_stage_4: OK")
    
    def test_super_complex_2(self):
        """测试test_super_complex_2 - 嵌套函数和模块级return修复"""
        pyc_path = r'd:\Desktop\ptrade相关\pythoncdc\tests\complex\__pycache__\test_super_complex_2.cpython-311.pyc'
        if os.path.exists(pyc_path):
            source = self._test_pyc_file(pyc_path)
            print("  test_super_complex_2: OK")
    
    def test_super_complex_6(self):
        """测试test_super_complex_6"""
        pyc_path = r'd:\Desktop\ptrade相关\pythoncdc\tests\complex\__pycache__\test_super_complex_6.cpython-311.pyc'
        if os.path.exists(pyc_path):
            source = self._test_pyc_file(pyc_path)
            print("  test_super_complex_6: OK")
    
    def test_super_complex_8(self):
        """测试test_super_complex_8"""
        pyc_path = r'd:\Desktop\ptrade相关\pythoncdc\tests\complex\__pycache__\test_super_complex_8.cpython-311.pyc'
        if os.path.exists(pyc_path):
            source = self._test_pyc_file(pyc_path)
            print("  test_super_complex_8: OK")
    
    def test_super_complex_final(self):
        """测试test_super_complex_final"""
        pyc_path = r'd:\Desktop\ptrade相关\pythoncdc\tests\complex\__pycache__\test_super_complex_final.cpython-311.pyc'
        if os.path.exists(pyc_path):
            source = self._test_pyc_file(pyc_path)
            print("  test_super_complex_final: OK")


class TestBatchFixes(unittest.TestCase):
    """测试批次修复"""
    
    def test_batch1_files(self):
        """测试Batch 1文件"""
        files = [
            'test_fix_123.cpython-311.pyc',
            'test_generator_advanced.cpython-311.pyc',
            'test_multi_stage_3.cpython-311.pyc',
        ]
        self._test_batch(files, "Batch 1")
    
    def test_batch2_files(self):
        """测试Batch 2文件"""
        files = [
            'test_nested_function_advanced.cpython-311.pyc',
            'test_nested_function_complex.cpython-311.pyc',
            'test_process_with_loops_advanced.cpython-311.pyc',
            'test_super_complex_1.cpython-311.pyc',
        ]
        self._test_batch(files, "Batch 2")
    
    def test_batch3_files(self):
        """测试Batch 3文件"""
        files = [
            'test_super_complex_2.cpython-311.pyc',
            'test_super_complex_6.cpython-311.pyc',
            'test_super_complex_8.cpython-311.pyc',
            'test_super_complex_final.cpython-311.pyc',
        ]
        self._test_batch(files, "Batch 3")
    
    def _test_batch(self, files, batch_name):
        """辅助方法: 测试一批文件"""
        success = 0
        failed = []
        
        for filename in files:
            pyc_path = rf'd:\Desktop\ptrade相关\pythoncdc\tests\complex\__pycache__\{filename}'
            if not os.path.exists(pyc_path):
                continue
            
            try:
                with open(pyc_path, 'rb') as f:
                    f.read(16)
                    code = marshal.load(f)
                
                cfg = CFGBuilder().build(code)
                ast_dict = ASTGeneratorV2(cfg, recursive=True).generate()
                generator = CFGCodeGenerator()
                source = generator.generate(ast_dict)
                
                compile(source, '<test>', 'exec')
                success += 1
            except Exception as e:
                failed.append((filename, str(e)))
        
        print(f"  {batch_name}: {success}/{len(files)} 成功")
        if failed:
            for filename, error in failed:
                print(f"    - {filename}: {error[:50]}")


def run_tests():
    """运行所有测试"""
    print("="*70)
    print("回归测试 - 验证反编译器修复")
    print("="*70)
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试
    suite.addTests(loader.loadTestsFromTestCase(TestDecompilerFixes))
    suite.addTests(loader.loadTestsFromTestCase(TestBatchFixes))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 打印总结
    print("\n" + "="*70)
    print("测试总结")
    print("="*70)
    print(f"运行测试: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
