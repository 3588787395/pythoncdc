"""
测试 try-except-finally 反编译
"""

import sys
sys.path.insert(0, r'd:\Desktop\ptrade相关\pythoncdc')

import dis
from core.cfg.cfg_builder import build_cfg
from core.cfg.structured_analyzer import StructuredAnalyzer
from core.cfg.ast_generator_v2 import ASTGeneratorV2
from core.cfg.ast_converter import CFGASTConverter
from core.cfg.code_generator import CFGCodeGenerator


def test_func():
    result = []
    try:
        result.append("try")
    except ValueError:
        result.append("except")
    finally:
        result.append("finally")
    return result


print("原始代码:")
print("""
def test_func():
    result = []
    try:
        result.append("try")
    except ValueError:
        result.append("except")
    finally:
        result.append("finally")
    return result
""")

print("原始函数字节码:")
dis.dis(test_func)

# 构建CFG
cfg = build_cfg(test_func.__code__, test_func.__name__)

# 结构化分析
analyzer = StructuredAnalyzer(cfg)
structures = analyzer.analyze()

# 生成AST
ast_gen = ASTGeneratorV2(cfg)
ast_gen.structures = structures
func_ast_dict = ast_gen.generate()

# 转换AST
converter = CFGASTConverter()
func_ast = converter.convert(func_ast_dict)

# 生成代码
code_gen = CFGCodeGenerator()
func_code_str = code_gen.generate(func_ast, in_function=True)

print("\n反编译代码:")
print(func_code_str)

# 验证反编译结果
expected_lines = [
    "try:",
    'result.append("try")',
    "except ValueError:",
    'result.append("except")',
    "finally:",
    'result.append("finally")'
]

print("\n验证结果:")
all_passed = True
for line in expected_lines:
    if line in func_code_str:
        print(f"  ✓ 找到: {line}")
    else:
        print(f"  ✗ 缺失: {line}")
        all_passed = False

# 检查finally块是否重复
finally_count = func_code_str.count('finally:')
if finally_count == 1:
    print(f"  ✓ finally块出现1次（正确）")
elif finally_count > 1:
    print(f"  ✗ finally块出现{finally_count}次（重复！）")
    all_passed = False
else:
    print(f"  ✗ finally块未找到")
    all_passed = False

if all_passed:
    print("\n✓ 所有测试通过！")
else:
    print("\n✗ 测试失败！")
