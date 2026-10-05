# rv3_02: B89 变体——模块级混合 boolop 链（or 外层 and 内层 / and 外层 or 内层）
_A = 1
_B = 2
_C = 3
_D = 4
_G = 5
_H = 6

X = _A or (_B and _C)
Y = (_A or _B) and _C
Z = _A or (_B and _C) or _D
W = (_A and _B) or (_C and _D) or _E if False else _G
V = _A < _B or (_C < _D and _E < _G) or _H
