# n2_02 负对照：简单 except* 单 handler（强制 MATCH）
# 焦点：except* 基础路径不回退（台账 §7 全链）


def f(tag):
    try:
        raise ExceptionGroup("g", [ValueError("v")])
    except* ValueError as e:
        tag = tag + "V"
    return tag
