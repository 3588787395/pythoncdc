import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR5WhileMatchInElse(ExhaustiveTestCase):
    SOURCE_CODE = """def f():
    while a:
        if b:
            break
    else:
        match x:
            case 1:
                y = 1
            case _:
                y = 2"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
