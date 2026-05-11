"""测试嵌套with语句的情况"""

# 测试1：简单的嵌套with语句
with open('file1.txt', 'r') as f1:
    with open('file2.txt', 'r') as f2:
        print(f1.read())
        print(f2.read())

# 测试2：多层嵌套with语句
with open('file1.txt', 'r') as f1:
    with open('file2.txt', 'r') as f2:
        with open('file3.txt', 'r') as f3:
            print(f1.read())
            print(f2.read())
            print(f3.read())

# 测试3：嵌套with语句中包含if语句
with open('file1.txt', 'r') as f1:
    with open('file2.txt', 'r') as f2:
        content1 = f1.read()
        content2 = f2.read()
        if content1 == content2:
            print('Files are identical')
        else:
            print('Files are different')

# 测试4：嵌套with语句中包含循环
with open('file1.txt', 'r') as f1:
    with open('file2.txt', 'r') as f2:
        for line1 in f1:
            for line2 in f2:
                if line1.strip() == line2.strip():
                    print(f'Match: {line1.strip()}')
