# 创建测试文件
with open('test.txt', 'w') as f:
    f.write('Hello')

with open('data.txt', 'w') as f:
    f.write('Line 1\nLine 2\nLine 3\n')

with open('file1.txt', 'w') as f:
    f.write('File 1 content')

with open('file2.txt', 'w') as f:
    f.write('File 2 content')

print("Test files created successfully!")
