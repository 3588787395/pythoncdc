import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR25AsyncWithAsyncForInElif(ExhaustiveTestCase):
    SOURCE_CODE = """async def f(items, mode):
    if mode == 'a':
        return 'a'
    elif mode == 'b':
        async with session() as s:
            async for item in s.iter():
                if item.is_valid():
                    await process(item)
            return 'done'
    else:
        return 'c' """
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
