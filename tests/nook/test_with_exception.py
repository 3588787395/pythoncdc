"""测试with语句中包含异常处理的情况"""

# 测试1：with语句中包含try-except
with open('test.txt', 'r') as f:
    try:
        content = f.read()
        result = int(content)
        print(f'Result: {result}')
    except ValueError:
        print('Invalid number')
    except Exception as e:
        print(f'Error: {e}')

# 测试2：with语句中包含try-finally
with open('test.txt', 'r') as f:
    try:
        content = f.read()
        print(content)
    finally:
        print('Cleanup')

# 测试3：with语句中包含try-except-else-finally
with open('test.txt', 'r') as f:
    try:
        content = f.read()
        result = int(content)
    except ValueError:
        print('Invalid number')
    else:
        print(f'Result: {result}')
    finally:
        print('Cleanup')
