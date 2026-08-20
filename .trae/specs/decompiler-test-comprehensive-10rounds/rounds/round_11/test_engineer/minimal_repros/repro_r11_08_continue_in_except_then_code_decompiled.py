# Source Generated with Decompyle++ (Python version)
# File: repro_r11_08_continue_in_except_then_code.pyc (Python 3.11)

data = [1, 'a', 2]
result = []
for item in data:
    try:
        x = int(item)
        result.append(x)
    except ValueError:
        result.append(0)
        continue
    print(f'ok: {item}')
