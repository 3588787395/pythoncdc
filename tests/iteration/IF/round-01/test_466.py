"""Round 01 IF - test 466"""
import sys
sys.path.insert(0, r"F:\Downloads\pythoncdc-main")
from core.cfg import decompile

SOURCE = 'x = z if y else z\nif x:\n    r = 1\nelif w:\n    r = 2'

def test_466():
    result = decompile(SOURCE)
    assert result is not None, "Decompilation returned None"
    compiled = compile(result, "<test>", "exec")