import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestW102(ExhaustiveTestCase):
    SOURCE_CODE = 'with ctx:\n    result = None\n    try:\n        result = compute()\n    except:\n        result = 0\n    finally:\n        cleanup()'
    REGION_TYPE = "WITH"
    def test_decompile(self):
        self.verify_decompilation()
