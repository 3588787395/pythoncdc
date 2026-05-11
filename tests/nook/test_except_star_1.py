"""
测试状态: ❌ 失败 (Python 3.11+)
优先级: P2
相关任务: 任务5.3

描述:
    测试 Python 3.11+ except* 语法 (Exception Groups)

当前问题:
    - 完全不支持 except* 语法
    - 不支持 ExceptionGroup 相关opcode

期望输出:
    应正确输出 except* ValueError: 语法
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tests.other.test_utils import DecompileTestCase, disassemble_code

import sys as sys_module

# 只在 Python 3.11+ 运行
if sys_module.version_info >= (3, 11):
    # 测试用例1: 基本 except*
    TEST_EXCEPT_STAR_BASIC = DecompileTestCase(
        name="except_star_basic",
        source_code='''
try:
    risky_operation()
except* ValueError:
    handle_value_error()
except* TypeError:
    handle_type_error()
'''.strip(),
        expected_patterns=["try:", "except* ValueError:", "except* TypeError:"]
    )

    # 测试用例2: except* with variable
    TEST_EXCEPT_STAR_VAR = DecompileTestCase(
        name="except_star_var",
        source_code='''
try:
    batch_process()
except* ValueError as eg:
    print(f"Value errors: {eg.exceptions}")
except* Exception as eg:
    print(f"Other errors: {eg.exceptions}")
'''.strip(),
        expected_patterns=["except* ValueError as eg:", "except* Exception as eg:"]
    )

    # 测试用例3: except* with else and finally
    TEST_EXCEPT_STAR_FULL = DecompileTestCase(
        name="except_star_full",
        source_code='''
try:
    process()
except* ValueError:
    handle_error()
else:
    print("Success")
finally:
    cleanup()
'''.strip(),
        expected_patterns=["except* ValueError:", "else:", "finally:"]
    )
else:
    print("跳过: 需要 Python 3.11+")
    TEST_EXCEPT_STAR_BASIC = None
    TEST_EXCEPT_STAR_VAR = None
    TEST_EXCEPT_STAR_FULL = None


if __name__ == "__main__":
    if sys_module.version_info < (3, 11):
        print("此测试需要 Python 3.11+")
        sys_module.exit(0)
    
    print("=" * 60)
    print("EXCEPT* 字节码示例")
    print("=" * 60)
    disassemble_code(TEST_EXCEPT_STAR_BASIC.source_code, "except_star_basic")
    
    print("\n" + "=" * 60)
    print("运行测试")
    print("=" * 60)
    
    for test in [TEST_EXCEPT_STAR_BASIC, TEST_EXCEPT_STAR_VAR, TEST_EXCEPT_STAR_FULL]:
        if test:
            success = test.run()
            print(test.get_report())
            print()
