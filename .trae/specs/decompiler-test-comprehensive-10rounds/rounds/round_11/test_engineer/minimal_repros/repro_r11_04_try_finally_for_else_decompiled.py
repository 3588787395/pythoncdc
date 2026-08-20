# Source Generated with Decompyle++ (Python version)
# File: repro_r11_04_try_finally_for_else.pyc (Python 3.11)

data = [1, 2, 3]
result = []
for item in data:
    try:
        result.append(item * 2)
    except Exception as e:
        result.append(f'error: {e}')
    finally:
        print(f'item: {item}')
