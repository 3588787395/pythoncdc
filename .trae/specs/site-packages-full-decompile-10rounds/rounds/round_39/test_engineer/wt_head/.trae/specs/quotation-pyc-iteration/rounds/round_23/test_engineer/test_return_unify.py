"""R23-N6: 测试 Python 编译器对 return 的处理"""
import dis

# 模式1: if-then 内有 return，外面也有 return
def f1(x):
    if x:
        a = 1
        return a
    else:
        a = 2
    a = 3
    return a

# 模式2: if-then 没有 return，外面有 return
def f2(x):
    if x:
        a = 1
    elif x > 5:
        a = 2
    else:
        a = 3
    return a

# 模式3: if-then-elif-else 内 if-then 有 return
def f3(x):
    if x is None:
        if x == 1:
            x = 4
        else:
            x -= 1
        a = str(x)
        return a
    elif x <= 5:
        x = 5
        x -= 1
    else:
        x = 5
    a = str(x)
    return a

print("=== f1 (if-then 内 return) ===")
dis.dis(f1)
print("\n=== f2 (if-elif-else 后 return) ===")
dis.dis(f2)
print("\n=== f3 (date_convert 模式) ===")
dis.dis(f3)
