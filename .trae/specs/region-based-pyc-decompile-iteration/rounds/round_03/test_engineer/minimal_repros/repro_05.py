# family: F6 — for-else 带 continue：else 子句被丢弃（变体 1，对应 convert.pyc getchnstr 的 `if A or B: continue` 形状）
# 预期字节码模式: FOR_ITER 循环体内 `if i > 0: continue`，循环结尾紧跟 else: return None
# 实际反编译输出: else 分支整体消失
# 关联 pyc: site-packages/fly/common/convert.pyc getchnstr（F6，continue 极性反转 + else 丢失）
# 判定: compile(本文件) -> decompile -> compile，递归比对所有 code object 的 co_code

def f(items):
    for i in items:
        if i > 0:
            continue
    else:
        return None
    return i
