# -*- coding: utf-8 -*-
"""R14-05 负对照：推导式**本身**就是嵌套的（合法嵌套，非兄弟）。

`[[x for x in row] for row in t]` 的字节码里第二个 MAKE_FUNCTION 出现在第一个
GET_ITER **之前**：
  LOAD_CONST <外层 listcomp>; MAKE_FUNCTION; LOAD_CONST <内层 listcomp>;
  MAKE_FUNCTION; LOAD_FAST t; GET_ITER; CALL; GET_ITER; CALL; RETURN
这才是 `comprehension_generator.py:111-144` chained-pair 探测器**本来**要认的形状。
实测：产物 `[[x for x in row] for row in t]` 严格一致。
期望：MATCH（负对照 —— 修复不得把合法嵌套一起改掉）。
"""


def genuine_nested(t):
    return [[x for x in row] for row in t]


def genuine_nested_dictcomp(t):
    return {k: [x for x in v] for k, v in t}
