"""测试with语句中包含循环的情况"""

# 测试1：with语句中包含for循环
with open('data.txt', 'r') as f:
    for line in f:
        print(line.strip())

# 测试2：with语句中包含while循环
with open('data.txt', 'r') as f:
    count = 0
    while count < 5:
        line = f.readline()
        if not line:
            break
        print(line.strip())
        count += 1

# 测试3：with语句中包含嵌套循环
with open('file1.txt', 'r') as f1:
    with open('file2.txt', 'r') as f2:
        for line1 in f1:
            for line2 in f2:
                if line1.strip() == line2.strip():
                    print(f'Match: {line1.strip()}')
