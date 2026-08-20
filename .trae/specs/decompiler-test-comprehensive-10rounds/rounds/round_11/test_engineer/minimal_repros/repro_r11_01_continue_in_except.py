# Repro 1: try-except inside for loop with continue in except block
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
