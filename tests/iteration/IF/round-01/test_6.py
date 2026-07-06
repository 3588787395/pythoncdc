"""Round 01 IF - test 6"""
import sys
sys.path.insert(0, r"F:\Downloads\pythoncdc-main")
from core.cfg import decompile

SOURCE = 'if x and a:\n    r = 1\nelif z:\n    r = 2\nelse:\n    r = 3'

def test_6():
    result = decompile(SOURCE)
    assert result is not None, "Decompilation returned None"
    compiled = compile(result, "<test>", "exec")