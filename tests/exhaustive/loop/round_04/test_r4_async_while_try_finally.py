import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR4AsyncWhileTryFinally(ExhaustiveTestCase):
    SOURCE_CODE = """async def f():
    while a:
        try:
            await do()
        finally:
            cleanup()"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
