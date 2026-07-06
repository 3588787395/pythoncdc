"""Round 01 IF - test 66"""
import sys
sys.path.insert(0, r"F:\Downloads\pythoncdc-main")
from core.cfg import decompile

SOURCE = 'if x or a:\n    r = 1\nelif z:\n    r = 2\nelse:\n    r = 3'

def test_66():
    result = decompile(SOURCE)
    assert result is not None, "Decompilation returned None"
    compiled = compile(result, "<test>", "exec")