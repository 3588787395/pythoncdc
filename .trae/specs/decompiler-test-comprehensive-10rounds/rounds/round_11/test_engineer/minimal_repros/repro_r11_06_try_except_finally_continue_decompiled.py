# Source Generated with Decompyle++ (Python version)
# File: repro_r11_06_try_except_finally_continue.pyc (Python 3.11)

data = [1, 'a', 2]
for item in data:
    try:
        pass
    except ValueError:
        print(f'error: {item}')
        print(f'done: {item}')
        x = int(item)
        continue
    finally:
        print(f'done: {item}')
