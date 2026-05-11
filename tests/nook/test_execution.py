# 测试反编译后的代码是否可以执行

# 创建测试文件
with open('test.txt', 'w') as f:
    f.write('Hello')

with open('data.txt', 'w') as f:
    f.write('Line 1\n')
    f.write('Line 2\n')
    f.write('Line 3\n')

# 测试1：基本with
with open('test.txt', 'w') as f:
    f.write('Hello')

# 测试2：with + for
with open('data.txt', 'r') as f:
    for line in f:
        print(line.strip())
