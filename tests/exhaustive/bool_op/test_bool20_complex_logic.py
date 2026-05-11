import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestBool20ComplexLogic(ExhaustiveTestCase):
    SOURCE_CODE = """if (user and user.is_active() and (user.has_permission('read') or user.is_admin()) and resource.exists()):
    access(resource)"""
    REGION_TYPE = "BOOL_OP"

    def test_decompile(self):
        self.verify_decompilation()
