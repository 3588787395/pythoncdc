"""
测试状态: ❌ 失败 (Python 3.12+)
优先级: P2
相关任务: 任务5.2

描述:
    测试 Python 3.12+ type 参数语句

当前问题:
    - 完全不支持 type 语句
    - 不支持泛型函数/类

期望输出:
    应正确输出 type Point[T] = ... 语法
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tests.other.test_utils import DecompileTestCase, disassemble_code

import sys as sys_module

# 只在 Python 3.12+ 运行
if sys_module.version_info >= (3, 12):
    # 测试用例1: type 语句
    TEST_TYPE_STMT = DecompileTestCase(
        name="type_stmt",
        source_code='''
type Point[T] = tuple[T, T]
type StringDict[V] = dict[str, V]
'''.strip(),
        expected_patterns=["type Point[T]", "type StringDict[V]"]
    )

    # 测试用例2: 泛型函数
    TEST_GENERIC_FUNC = DecompileTestCase(
        name="generic_func",
        source_code='''
def func[T](x: T) -> T:
    return x

def pair[T, U](a: T, b: U) -> tuple[T, U]:
    return (a, b)
'''.strip(),
        expected_patterns=["def func[T]", "def pair[T, U]"]
    )

    # 测试用例3: 泛型类
    TEST_GENERIC_CLASS = DecompileTestCase(
        name="generic_class",
        source_code='''
class Container[G]:
    def __init__(self, value: G):
        self.value = value
    
    def get(self) -> G:
        return self.value
'''.strip(),
        expected_patterns=["class Container[G]:", "def get(self) -> G:"]
    )
else:
    print("跳过: 需要 Python 3.12+")
    TEST_TYPE_STMT = None
    TEST_GENERIC_FUNC = None
    TEST_GENERIC_CLASS = None


if __name__ == "__main__":
    if sys_module.version_info < (3, 12):
        print("此测试需要 Python 3.12+")
        sys_module.exit(0)
    
    print("=" * 60)
    print("TYPE 参数语句字节码示例")
    print("=" * 60)
    disassemble_code(TEST_TYPE_STMT.source_code, "type_stmt")
    
    print("\n" + "=" * 60)
    print("运行测试")
    print("=" * 60)
    
    for test in [TEST_TYPE_STMT, TEST_GENERIC_FUNC, TEST_GENERIC_CLASS]:
        if test:
            success = test.run()
            print(test.get_report())
            print()
