"""Round 01 IF - test 414"""
import sys
sys.path.insert(0, r"F:\Downloads\pythoncdc-main")
from core.cfg import decompile

SOURCE = 'if a or b:\n    r = 1\nelif c0:\n    r = 2\nelif c1:\n    r = 3\nelif c2:\n    r = 4'

def test_414():
    result = decompile(SOURCE)
    assert result is not None, "Decompilation returned None"
    compiled = compile(result, "<test>", "exec")