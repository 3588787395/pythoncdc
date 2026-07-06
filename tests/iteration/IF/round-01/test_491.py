"""Round 01 IF - test 491"""
import sys
sys.path.insert(0, r"F:\Downloads\pythoncdc-main")
from core.cfg import decompile

SOURCE = 'if 0 < a < 10:\n    r = 1\nelif a > 20:\n    r = 2\nelse:\n    r = 3'

def test_491():
    result = decompile(SOURCE)
    assert result is not None, "Decompilation returned None"
    compiled = compile(result, "<test>", "exec")