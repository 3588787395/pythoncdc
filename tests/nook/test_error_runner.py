"""
错误驱动测试运行器 - 测试反编译错误驱动实例
"""

import os
import sys
import marshal
import py_compile
import traceback

sys.path.insert(0, r'd:\Desktop\ptrade相关\pythoncdc')

from core.cfg.cfg_builder import build_cfg
from core.cfg.structured_analyzer import StructuredAnalyzer
from core.cfg.ast_generator_v2 import ASTGeneratorV2
from core.cfg.ast_converter import CFGASTConverter
from core.cfg.code_generator import CFGCodeGenerator


def test_single_file(py_file: str) -> dict:
    """测试单个文件"""
    result = {
        'file': os.path.basename(py_file),
        'success': False,
        'functions': 0,
        'errors': []
    }
    
    try:
        # 编译
        pyc_file = py_file + 'c'
        py_compile.compile(py_file, pyc_file, doraise=True)
        
        # 读取pyc
        with open(pyc_file, 'rb') as f:
            f.read(16)
            code_obj = marshal.load(f)
        
        # 获取所有函数
        func_codes = [c for c in code_obj.co_consts if hasattr(c, 'co_code')]
        result['functions'] = len(func_codes)
        
        for func_code in func_codes:
            try:
                cfg = build_cfg(func_code, func_code.co_name)
                analyzer = StructuredAnalyzer(cfg)
                structures = analyzer.analyze()
                
                ast_gen = ASTGeneratorV2(cfg)
                ast_gen.structures = structures
                func_ast_dict = ast_gen.generate()
                
                if not func_ast_dict:
                    result['errors'].append(f"{func_code.co_name}: AST生成失败")
                    continue
                
                converter = CFGASTConverter()
                func_ast = converter.convert(func_ast_dict)
                
                if not func_ast:
                    result['errors'].append(f"{func_code.co_name}: AST转换失败")
                    continue
                
                code_gen = CFGCodeGenerator()
                func_code_str = code_gen.generate(func_ast, in_function=True)
                
            except Exception as e:
                result['errors'].append(f"{func_code.co_name}: {str(e)}")
        
        if not result['errors']:
            result['success'] = True
            
    except Exception as e:
        result['errors'].append(f"文件处理失败: {str(e)}")
    
    return result


def main():
    print("="*70)
    print("CFG错误驱动反编译测试")
    print("="*70)
    
    test_file = r'd:\Desktop\ptrade相关\pythoncdc\tests\loop\test_error_driven.py'
    
    print(f"\n测试文件: {os.path.basename(test_file)}\n")
    
    result = test_single_file(test_file)
    
    status = "PASS" if result['success'] else "FAIL"
    symbol = "✓" if result['success'] else "✗"
    print(f"{symbol} {result['file']:35s} [{status}] 函数:{result['functions']:2d}")
    
    if not result['success']:
        for error in result['errors'][:10]:
            print(f"    ! {error}")
    
    print(f"\n{'='*70}")
    print(f"结果: {'通过' if result['success'] else '失败'}")
    print(f"{'='*70}")
    
    return result['success']


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
