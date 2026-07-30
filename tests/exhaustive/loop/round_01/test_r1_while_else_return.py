import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR1WhileElseReturn(ExhaustiveTestCase):
    SOURCE_CODE = """def f():
    while a:
        if b:
            break
    else:
        return 1
    return 2"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
