import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR2ForElseMultiStmtModule(ExhaustiveTestCase):
    SOURCE_CODE = """for i in r:
    if i:
        break
else:
    a = 1
    b = 2"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
