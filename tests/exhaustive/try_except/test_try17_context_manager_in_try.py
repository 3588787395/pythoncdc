import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTry17ContextManagerInTry(ExhaustiveTestCase):
    SOURCE_CODE = """try:
    with open(f) as fh:
        data = fh.read()
    process(data)
except IOError:
    use_default()"""
    REGION_TYPE = "TRY_EXCEPT"

    def test_decompile(self):
        self.verify_decompilation()
