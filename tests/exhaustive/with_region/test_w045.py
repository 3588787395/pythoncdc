import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestW045(ExhaustiveTestCase):
    SOURCE_CODE = "with open('f') as f:\n    try:\n        x = f.read()\n    except IOError:\n        x = ''\n    else:\n        y = len(x)"
    REGION_TYPE = "WITH"
    def test_decompile(self):
        self.verify_decompilation()
