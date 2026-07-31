import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR6ForElseBreakOuter(ExhaustiveTestCase):
    SOURCE_CODE = """for i in range(5):
    for j in range(5):
        if j == 3 and i == 2:
            break
    else:
        continue
    break"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
