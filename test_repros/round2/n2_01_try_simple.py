# n2_01 负对照：简单 try/except 单 handler（强制 MATCH）
# 焦点：基础异常区域在本轮新语料下不回退


def f(d):
    try:
        return d["k"]
    except KeyError:
        return 0
