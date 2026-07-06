import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestWhile08ComplexCond(ExhaustiveTestCase):
    SOURCE_CODE = """while len(queue) > 0 and queue[0].priority < max_p:
    process(queue.pop(0))"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
