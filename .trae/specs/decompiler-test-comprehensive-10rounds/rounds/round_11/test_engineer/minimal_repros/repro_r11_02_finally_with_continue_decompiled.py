# Source Generated with Decompyle++ (Python version)
# File: repro_r11_02_finally_with_continue.pyc (Python 3.11)

data = [1, 'a', 2]
result = []
for item in data:
    try:
        pass
    except ValueError:
        result.append(f'error: {item}')
        print(f'processed: {item}')
        converted = int(item)
        result.append(converted)
        continue
    except Exception as e:
        result.append(f'outer error: {e}')
    finally:
        print(f'processed: {item}')
