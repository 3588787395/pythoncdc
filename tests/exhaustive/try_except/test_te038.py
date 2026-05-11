import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestTE038(ExhaustiveTestCase):
    SOURCE_CODE = "try:\n    with open('f') as f:\n        data = f.read()\n        lines = data.split('\\n')\nexcept:\n    lines = []"
    REGION_TYPE = "TRY_EXCEPT"
    def test_decompile(self):
        self.verify_decompilation()
