"""
测试状态: ⚠️ 部分
优先级: P2
相关任务: 任务5.1

描述:
    测试扩展 del 语句支持

当前问题:
    - 不支持元组解包删除: del a, b, c
    - 不支持切片删除: del lst[1:3]

期望输出:
    应正确输出各种del语句形式
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tests.other.test_utils import DecompileTestCase, disassemble_code


# 测试用例1: 元组解包删除
TEST_DEL_TUPLE = DecompileTestCase(
    name="del_tuple",
    source_code='''
def cleanup(a, b, c):
    del a, b, c
'''.strip(),
    expected_patterns=["del a, b, c"]
)

# 测试用例2: 切片删除
TEST_DEL_SLICE = DecompileTestCase(
    name="del_slice",
    source_code='''
def remove_range(lst):
    del lst[1:3]
    del lst[::2]
'''.strip(),
    expected_patterns=["del lst[1:3]", "del lst[::2]"]
)

# 测试用例3: 属性删除
TEST_DEL_ATTR = DecompileTestCase(
    name="del_attr",
    source_code='''
def remove_attr(obj):
    del obj.temporary
    del obj.data.value
'''.strip(),
    expected_patterns=["del obj.temporary", "del obj.data.value"]
)


if __name__ == "__main__":
    print("=" * 60)
    print("DEL 语句字节码示例")
    print("=" * 60)
    disassemble_code(TEST_DEL_TUPLE.source_code, "del_tuple")
    
    print("\n" + "=" * 60)
    print("运行测试")
    print("=" * 60)
    
    for test in [TEST_DEL_TUPLE, TEST_DEL_SLICE, TEST_DEL_ATTR]:
        success = test.run()
        print(test.get_report())
        print()
