"""Round 01 IF - test 78"""
import sys
sys.path.insert(0, r"F:\Downloads\pythoncdc-main")
from core.cfg import decompile

SOURCE = 'if y or b:\n    r = 1\nelif z:\n    r = 2\nelse:\n    r = 3'

def test_78():
    result = decompile(SOURCE)
    assert result is not None, "Decompilation returned None"
    compiled = compile(result, "<test>", "exec")