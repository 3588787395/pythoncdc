"""Round 01 IF - test 308"""
import sys
sys.path.insert(0, r"F:\Downloads\pythoncdc-main")
from core.cfg import decompile

SOURCE = 'if 0 > x < 10 or z > 0:\n    r = 1\nelif z:\n    r = 2'

def test_308():
    result = decompile(SOURCE)
    assert result is not None, "Decompilation returned None"
    compiled = compile(result, "<test>", "exec")