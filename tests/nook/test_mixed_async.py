"""
测试混合同步/异步代码的反编译

测试状态: 🔄 待验证
优先级: P1

描述:
    测试同步和异步代码混合场景的正确反编译

期望输出:
    - 同步和异步函数定义正确区分
    - 混用场景下关键字正确保留
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tests.async_tests.test_utils import AsyncTestCase, run_test_suite, print_test_summary


# 测试用例1: 同步函数调用异步函数
TEST_SYNC_CALLS_ASYNC = AsyncTestCase(
    name="sync_calls_async",
    source_code='''
import asyncio

def run_async_task():
    result = asyncio.run(async_task())
    return result

async def async_task():
    return "done"
'''.strip(),
    expected_patterns=["def run_async_task", "async def async_task", "asyncio.run"]
)

# 测试用例2: 异步函数中使用同步代码
TEST_ASYNC_USES_SYNC = AsyncTestCase(
    name="async_uses_sync",
    source_code='''
def sync_helper(x):
    return x * 2

async def async_processor():
    data = await fetch_data()
    processed = sync_helper(data)
    return processed
'''.strip(),
    expected_patterns=["def sync_helper", "async def async_processor", "await fetch_data", "sync_helper(data)"]
)

# 测试用例3: 类中的同步和异步方法
TEST_CLASS_MIXED_METHODS = AsyncTestCase(
    name="class_mixed_methods",
    source_code='''
class DataProcessor:
    def __init__(self):
        self.data = []
    
    def sync_process(self, item):
        return item.upper()
    
    async def async_fetch(self):
        self.data = await fetch_from_db()
    
    async def process_all(self):
        await self.async_fetch()
        return [self.sync_process(item) for item in self.data]
'''.strip(),
    expected_patterns=["class DataProcessor", "def __init__", "def sync_process", "async def async_fetch", "async def process_all"]
)

# 测试用例4: 同步生成器和异步生成器共存
TEST_MIXED_GENERATORS = AsyncTestCase(
    name="mixed_generators",
    source_code='''
def sync_gen():
    for i in range(5):
        yield i

async def async_gen():
    for i in range(5):
        await asyncio.sleep(0.01)
        yield i

async def use_both():
    sync_results = list(sync_gen())
    async_results = [x async for x in async_gen()]
    return sync_results, async_results
'''.strip(),
    expected_patterns=["def sync_gen", "async def async_gen", "yield i", "async for"]
)

# 测试用例5: 复杂混合场景
TEST_COMPLEX_MIXED = AsyncTestCase(
    name="complex_mixed",
    source_code='''
import asyncio

class Manager:
    def __init__(self):
        self.items = []
    
    def add_item(self, item):
        self.items.append(item)
    
    async def load_items(self):
        async for item in fetch_items():
            self.add_item(item)
    
    def get_items(self):
        return self.items.copy()

async def main():
    manager = Manager()
    await manager.load_items()
    return manager.get_items()

def run():
    return asyncio.run(main())
'''.strip(),
    expected_patterns=["class Manager", "def __init__", "def add_item", "async def load_items", "def get_items", "async def main", "def run"]
)


if __name__ == "__main__":
    print("=" * 60)
    print("混合同步/异步代码测试")
    print("=" * 60)
    
    test_cases = [
        TEST_SYNC_CALLS_ASYNC,
        TEST_ASYNC_USES_SYNC,
        TEST_CLASS_MIXED_METHODS,
        TEST_MIXED_GENERATORS,
        TEST_COMPLEX_MIXED,
    ]
    
    results = run_test_suite(test_cases)
    
    for detail in results['details']:
        print("\n" + detail['report'])
    
    print_test_summary(results)
