# Source Generated with Decompyle++ (Python version)
# File: repro_r11_01_continue_in_except.pyc (Python 3.11)

data = [1, 'a', 2]
result = []
for item in data:
    try:
        converted = int(item)
        result.append(converted)
    except ValueError:
        result.append(f'error: {item}')
        continue
    print(f'processed: {item}')
