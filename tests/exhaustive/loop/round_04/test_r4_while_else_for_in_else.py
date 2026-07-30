import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR4WhileElseForInElse(ExhaustiveTestCase):
    SOURCE_CODE = """def f():
    while a:
        if b:
            break
    else:
        for j in s:
            x = j"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
