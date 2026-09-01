"""R23-N6: 测试 Python 编译器 return 统一化"""
import dis
import sys

print(f"Python version: {sys.version}")

# 模式A: if-then 末尾 return data_return
def fA(x):
    if x is None:
        a = 1
        return a
    elif x > 5:
        a = 2
    else:
        a = 3
    a = a + 10
    return a

# 模式B: 跟 date_convert 完全一致的结构
def fB(x):
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

print("\n=== fA (简单 return in if-then) ===")
dis.dis(fA)
print("\n=== fB (date_convert 模式 + return) ===")
dis.dis(fB)
