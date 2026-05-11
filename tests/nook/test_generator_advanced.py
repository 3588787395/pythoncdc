"""Round 52: 高级生成器"""
from typing import Iterator, List

def chain_generators(*generators: Iterator[int]) -> Iterator[int]:
    """链接多个生成器"""
    for gen in generators:
        yield from gen

def test_chain_generators():
    def gen1():
        yield 1
        yield 2
    def gen2():
        yield 3
        yield 4
    result = list(chain_generators(gen1(), gen2()))
    assert result == [1, 2, 3, 4]
