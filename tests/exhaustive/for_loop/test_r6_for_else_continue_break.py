import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR6ForElseContinueBreak(ExhaustiveTestCase):
    SOURCE_CODE = """for i in range(3):
    for j in range(3):
        if j == 1:
            break
    else:
        continue
    break"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
