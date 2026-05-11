import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestW30WithCustomCtx(ExhaustiveTestCase):
    SOURCE_CODE = """class Ctx:
    def __enter__(self): return self
    def __exit__(self, *a): pass
with Ctx() as c:
    pass"""
    REGION_TYPE = "WITH_REGION"

    def test_decompile(self):
        self.verify_decompilation()
