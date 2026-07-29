"""测试: for 循环内 if-not 结构的 bytecode 生成"""
import dis

# Pattern 1: if-not with all-continue body, followed by statement
def f1(data):
    out = []
    for i in data:
        if not i == 'skip':
            if i == 'a':
                continue
            elif isinstance(i, dict):
                continue
            else:
                continue
        out.append(i)
    return out

# Pattern 2: separate if-continue statements
def f2(data):
    out = []
    for i in data:
        if i == 'skip':
            continue
        if i == 'a':
            continue
        elif isinstance(i, dict):
            continue
        else:
            continue
        out.append(i)
    return out

# Pattern 3: if-not with else-continue
def f3(data):
    out = []
    for i in data:
        if not i == 'skip':
            if i == 'a':
                continue
            elif isinstance(i, dict):
                continue
            else:
                continue
        else:
            continue
        out.append(i)
    return out

print("=== f1 (if-not, all-continue body, then statement) ===")
dis.dis(f1)
print("\n=== f2 (separate if-continue) ===")
dis.dis(f2)
print("\n=== f3 (if-not with else-continue) ===")
dis.dis(f3)
