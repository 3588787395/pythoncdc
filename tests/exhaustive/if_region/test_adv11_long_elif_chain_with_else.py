import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv11LongElifChainWithElse(ExhaustiveTestCase):
    # if 长 elif 链 + else (5 elif + else)
    SOURCE_CODE = """if a:
    pass
elif b:
    pass
elif d:
    pass
elif e:
    pass
elif f:
    pass
else:
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
