# Source Generated with Decompyle++ (Python version)
# File: repro_r11_09_try_except_continue_finally_else.pyc (Python 3.11)

data = [1, 'a', 2]
result = []
for item in data:
    try:
        pass
    except ValueError:
        result.append(0)
        print(f'item: {item}')
        print(f'result: {result}')
        break
        x = int(item)
        result.append(x)
        continue
    except Exception as e:
        result.append(f'error: {e}')
    finally:
        print(f'item: {item}')
