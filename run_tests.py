import sys
import os

sys.path.insert(0, r'f:\pythoncdc')
os.chdir(r'f:\pythoncdc')

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.code_generator import CodeGenerator

def decompile_source(source_code):
    original_code = compile(source_code, '<test>', 'exec')
    cfg_builder = CFGBuilder()
    cfg = cfg_builder.build(original_code)
    analyzer = RegionAnalyzer(cfg)
    generator = RegionASTGenerator(cfg, analyzer)
    result = generator.generate()
    code_gen = CodeGenerator()
    return code_gen.generate(result)

def test_case(source_code, test_name):
    print(f"=" * 60)
    print(f"Testing: {test_name}")
    print(f"Source:\n{source_code}")
    print("=" * 60)
    try:
        result = decompile_source(source_code)
        print(f"Generated:\n{result}")
        try:
            compiled = compile(result, '<generated>', 'exec')
            print("Result: COMPILE OK")
            return True
        except SyntaxError as e:
            print(f"Result: SYNTAX ERROR - {e}")
            return False
    except Exception as e:
        print(f"Result: ERROR - {e}")
        import traceback
        traceback.print_exc()
        return False

# Test cases
source1 = "try:\n    pass\nfinally:\n    pass"
result1 = test_case(source1, "te04tryfinally")

print()
print()

source2 = "try:\n    while x < 3:\n        x += 1\nexcept:\n    y = 1"
result2 = test_case(source2, "te027")

print()
print("=" * 60)
print("Summary:")
print("=" * 60)
print(f"te04tryfinally: {'PASS' if result1 else 'FAIL'}")
print(f"te027: {'PASS' if result2 else 'FAIL'}")
