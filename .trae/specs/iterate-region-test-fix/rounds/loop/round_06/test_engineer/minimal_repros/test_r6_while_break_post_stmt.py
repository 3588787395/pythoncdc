import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR6WhileBreakPostStmt(ExhaustiveTestCase):
    SOURCE_CODE = """n = 0
while n < 10:
    n += 1
    if n == 5:
        break
    print(n)
print('end')"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
