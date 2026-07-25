import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR25AsyncForBreakInIfBody(ExhaustiveTestCase):
    SOURCE_CODE = """async def f(items):
    if items:
        async for x in items:
            if x == 'stop':
                break
            process(x)
        return 'done'
    else:
        return 'empty' """
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
