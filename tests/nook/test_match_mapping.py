"""
测试状态: ❌ 失败
优先级: P0
相关任务: 任务1.4

描述:
    测试 match/case 的映射模式匹配
    使用 MATCH_MAPPING 和 MATCH_KEYS 字节码指令

当前问题:
    - 完全不支持 MATCH_MAPPING/MATCH_KEYS 指令
    - 无法识别 {"key": value} 这样的映射模式

期望输出:
    应包含 case {"name": str(name)}: 这样的映射模式匹配
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tests.other.test_utils import DecompileTestCase, disassemble_code


# 测试用例1: 基本字典模式
TEST_MATCH_MAPPING_BASIC = DecompileTestCase(
    name="match_mapping_basic",
    source_code='''
data = {"name": "Alice", "age": 30}

match data:
    case {}:
        result = "empty dict"
    case {"name": str(name)}:
        result = f"name is {name}"
    case {"name": name, "age": age}:
        result = f"{name} is {age} years old"
    case _:
        result = "other"
'''.strip(),
    expected_patterns=["match", 'case {}:', 'case {"name":', "result"]
)

# 测试用例2: 带双星号的映射解包
TEST_MATCH_MAPPING_STAR = DecompileTestCase(
    name="match_mapping_star",
    source_code='''
config = {"host": "localhost", "port": 8080, "debug": True}

match config:
    case {"host": host, **rest}:
        result = f"host={host}, other={rest}"
    case {"port": port, **rest}:
        result = f"port={port}, other={rest}"
    case {**all_config}:
        result = f"all: {all_config}"
'''.strip(),
    expected_patterns=["match", 'case {"host": host, **rest}:', "result"]
)

# 测试用例3: 嵌套映射模式
TEST_MATCH_MAPPING_NESTED = DecompileTestCase(
    name="match_mapping_nested",
    source_code='''
user = {
    "name": "Bob",
    "address": {"city": "Beijing", "zip": "100000"}
}

match user:
    case {"name": name, "address": {"city": city}}:
        result = f"{name} lives in {city}"
    case {"name": name, "address": addr}:
        result = f"{name} has address {addr}"
    case {"name": name}:
        result = f"user {name}"
'''.strip(),
    expected_patterns=["match", '"address": {"city": city}', "result"]
)


if __name__ == "__main__":
    print("=" * 60)
    print("MATCH_MAPPING 字节码示例")
    print("=" * 60)
    disassemble_code(TEST_MATCH_MAPPING_BASIC.source_code, "match_mapping_basic")
    
    print("\n" + "=" * 60)
    print("运行测试")
    print("=" * 60)
    
    for test in [TEST_MATCH_MAPPING_BASIC, TEST_MATCH_MAPPING_STAR, TEST_MATCH_MAPPING_NESTED]:
        success = test.run()
        print(test.get_report())
        print()
