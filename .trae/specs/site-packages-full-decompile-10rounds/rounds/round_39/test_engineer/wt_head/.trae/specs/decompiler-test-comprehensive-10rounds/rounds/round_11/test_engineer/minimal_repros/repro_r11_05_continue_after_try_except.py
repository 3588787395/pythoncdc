# Repro 5: continue after try-except in for loop
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
