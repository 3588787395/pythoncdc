"""简单测试 - with语句中包含if语句"""
with open('test.txt', 'r') as f:
    content = f.read()
    if len(content) > 100:
        print('Large')
    else:
        print('Small')
