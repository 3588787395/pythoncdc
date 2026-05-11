import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTry19ContinueInTry(ExhaustiveTestCase):
    SOURCE_CODE = """while queue:
    try:
        item = queue.pop(0)
        if skip(item):
            continue
        process(item)
    except EmptyError:
        break"""
    REGION_TYPE = "TRY_EXCEPT"

    def test_decompile(self):
        self.verify_decompilation()
