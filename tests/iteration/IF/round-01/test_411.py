"""Round 01 IF - test 411"""
import sys
sys.path.insert(0, r"F:\Downloads\pythoncdc-main")
from core.cfg import decompile

SOURCE = 'if a and b:\n    r = 1\nelif c0:\n    r = 2\nelif c1:\n    r = 3'

def test_411():
    result = decompile(SOURCE)
    assert result is not None, "Decompilation returned None"
    compiled = compile(result, "<test>", "exec")