"""
测试状态: ⚠️ 部分
优先级: P1
相关任务: 任务3.1

描述:
    测试深层嵌套 if/elif/else (4层以上) 的正确识别

当前问题:
    - 4层以上嵌套时可能出现误判
    - elif链可能被错误识别为嵌套if

期望输出:
    应正确识别所有elif分支，而不是嵌套if
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tests.other.test_utils import DecompileTestCase, disassemble_code


# 测试用例1: 4层嵌套if
TEST_NESTED_IF_4LEVEL = DecompileTestCase(
    name="nested_if_4level",
    source_code='''
def classify(x):
    if x > 0:
        if x > 10:
            if x > 100:
                if x > 1000:
                    return "very large"
                return "large"
            return "medium"
        return "small"
    return "non-positive"
'''.strip(),
    expected_patterns=["if x > 0:", "if x > 10:", "if x > 100:", "if x > 1000:", "return"]
)

# 测试用例2: 长elif链
TEST_LONG_ELIF_CHAIN = DecompileTestCase(
    name="long_elif_chain",
    source_code='''
def get_grade(score):
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    elif score >= 50:
        return "E"
    else:
        return "F"
'''.strip(),
    expected_patterns=["if score >= 90:", "elif score >= 80:", "elif score >= 70:", "else:", "return"]
)

# 测试用例3: 混合嵌套和elif
TEST_MIXED_NESTED_ELIF = DecompileTestCase(
    name="mixed_nested_elif",
    source_code='''
def complex_logic(x, y):
    if x > 0:
        if y > 0:
            return "Q1"
        elif y < 0:
            return "Q4"
        else:
            return "on x-axis"
    elif x < 0:
        if y > 0:
            return "Q2"
        elif y < 0:
            return "Q3"
        else:
            return "on x-axis"
    else:
        return "on y-axis"
'''.strip(),
    expected_patterns=["if x > 0:", "elif x < 0:", "if y > 0:", "elif y < 0:", "else:", "return"]
)


if __name__ == "__main__":
    print("=" * 60)
    print("深层嵌套IF字节码示例")
    print("=" * 60)
    disassemble_code(TEST_LONG_ELIF_CHAIN.source_code, "long_elif_chain")
    
    print("\n" + "=" * 60)
    print("运行测试")
    print("=" * 60)
    
    for test in [TEST_NESTED_IF_4LEVEL, TEST_LONG_ELIF_CHAIN, TEST_MIXED_NESTED_ELIF]:
        success = test.run()
        print(test.get_report())
        print()
