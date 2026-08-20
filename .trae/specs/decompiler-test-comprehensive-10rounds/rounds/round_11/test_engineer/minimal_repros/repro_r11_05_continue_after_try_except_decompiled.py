# Source Generated with Decompyle++ (Python version)
# File: repro_r11_05_continue_after_try_except.pyc (Python 3.11)

data = [1, 'a', 2]
result = []
for item in data:
    try:
        converted = int(item)
    except ValueError:
        result.append(f'error: {item}')
        continue
    result.append(converted)
    print(f'processed: {item}')
