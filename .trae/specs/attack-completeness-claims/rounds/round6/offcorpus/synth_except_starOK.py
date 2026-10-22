# Source Generated with Decompyle++ (Python version)
# File: synth_except_star.pyc (Python 3.11)

__doc__ = """语料外**合成**补样：PEP 654 `except*`（ExceptionGroup）。

理由：本机 CPython 3.11 标准库（795 个文件）与 site-packages（14237 个文件）
经 AST 全量扫描，**真实 `except*` 语句数为 0**（唯一命中是 ast.py 里
`"except*"` 这个**字符串字面量**）⇒ 真实语料无法覆盖该特征，
故单列一件 origin=synthetic 的补样，只用于**测量**（不计入「真实语料」口径）。
"""
def f(items):
    total = 0
    try:
        for it in items:
            if it < 0:
                raise ValueError('neg')
            total += it
    except* ValueError as eg:
        total += len(eg.exceptions)
    except* TypeError:
        total = -1
    return total
def g(items):
    out = []
    try:
        for it in items:
            if isinstance(it, int):
                raise TypeError('int')
            out.append(it)
    except* TypeError as eg:
        out.append(len(eg.exceptions))
    return out
def main():
    print(f([1, 2, 3]))
    print(f([1, -2, 3]))
    print(g(['a', 'b']))
    print(g([1, 'b']))
