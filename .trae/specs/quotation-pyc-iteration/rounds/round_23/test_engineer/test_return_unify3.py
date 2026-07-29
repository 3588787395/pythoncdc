"""R23-N6: 测试 return 统一化的边界条件"""
import dis

# 测试: 简单 if-else 内 return
def g1(x):
    if x:
        return 1
    return 2

# 测试: if-elif-else 内 return
def g2(x):
    if x:
        return 1
    elif x > 5:
        return 2
    else:
        return 3

# 测试: if-elif-else 内 return (else 没有 return)
def g3(x):
    if x:
        return 1
    elif x > 5:
        return 2
    else:
        a = 3
    return a

# 测试: if-then 内 return + 共享 return
def g4(x):
    if x:
        a = 1
        return a
    a = 2
    return a

print("=== g1 ===")
dis.dis(g1)
print("\n=== g2 ===")
dis.dis(g2)
print("\n=== g3 ===")
dis.dis(g3)
print("\n=== g4 ===")
dis.dis(g4)
