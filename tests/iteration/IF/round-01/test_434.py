"""Round 01 IF - test 434"""
import sys
sys.path.insert(0, r"F:\Downloads\pythoncdc-main")
from core.cfg import decompile

SOURCE = 'if 0 < a < 10 or x > 100:\n    r = 1\nelif 0 < b < 20 or y > 200:\n    r = 2'

def test_434():
    result = decompile(SOURCE)
    assert result is not None, "Decompilation returned None"
    compiled = compile(result, "<test>", "exec")