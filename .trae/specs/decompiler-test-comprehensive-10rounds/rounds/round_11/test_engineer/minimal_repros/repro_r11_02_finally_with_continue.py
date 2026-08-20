# Repro 2: try-except-finally inside for loop with continue in except
data = [1, 'a', 2]
result = []
for item in data:
    try:
        converted = int(item)
        result.append(converted)
    except ValueError:
        result.append(f'error: {item}')
        continue
    except Exception as e:
        result.append(f'outer error: {e}')
    finally:
        print(f'processed: {item}')
