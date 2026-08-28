# family: F6 — `for ... else:` 的 else 子句被丢弃
# 预期字节码模式: FOR_ITER 之后紧跟 else 分支（return None），再落到循环后代码
# 实际反编译输出: else 分支整体消失
# 关联 pyc: site-packages/fly/common/convert.pyc getchnstr（循环内 continue 形状还原不同，jump=2 true=3）
# 判定: compile(本文件) -> decompile -> compile，递归比对所有 code object 的 co_code
# 直接复用 round_02 repro_10。

def f(items):
    for i in items:
        if i > 0:
            break
    else:
        return None
    return i
