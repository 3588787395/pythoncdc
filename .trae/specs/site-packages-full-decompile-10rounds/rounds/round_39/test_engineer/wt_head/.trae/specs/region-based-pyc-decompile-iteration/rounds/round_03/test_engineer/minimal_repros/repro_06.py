# family: F6 — while-else：else 子句被丢弃（变体 2，验证 while/else 同族问题）
# 预期字节码模式: 循环正常结束（不 break）后落到 else 分支
# 实际反编译输出: else 分支整体消失
# 关联 pyc: 与 F6 同族（for/else、while/else 在区域归约时并入循环出口）
# 判定: compile(本文件) -> decompile -> compile，递归比对所有 code object 的 co_code

def f(x):
    while x > 0:
        x -= 1
    else:
        return None
    return x
