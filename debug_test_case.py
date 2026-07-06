#!/usr/bin/env python
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tempfile
import ast
from tests.control_flow_matrix.base import ControlFlowTestCase

def debug_test_case():
    source_code = """if a > 0:
    with open("f") as f:
        a = f.read()"""
    
    print("=== Source Code ===")
    print(source_code)
    
    # Compile to bytecode
    print("\n=== Compiling ===")
    tree = ast.parse(source_code)
    code_obj = compile(tree, '<test>', 'exec')
    
    # Create test case instance
    test_instance = ControlFlowTestCase()
    test_instance.SOURCE_CODE = source_code
    
    print("\n=== Getting Region Analysis ===")
    try:
        decompiled = test_instance.decompile()
        print("\n=== Decompiled ===")
        print(repr(decompiled))
        print("\n=== Pretty Decompiled ===")
        print(decompiled)
        
        # 验证语法
        print("\n=== 验证语法 ===")
        try:
            parsed_decompiled = ast.parse(decompiled)
            print("语法检查通过")
        except Exception as e:
            print(f"语法检查失败: {e}")
            import traceback
            traceback.print_exc()
    except Exception as e:
        import traceback
        print(f"\n=== Error ===")
        print(traceback.format_exc())
    
    return test_instance

if __name__ == "__main__":
    test_case = debug_test_case()
