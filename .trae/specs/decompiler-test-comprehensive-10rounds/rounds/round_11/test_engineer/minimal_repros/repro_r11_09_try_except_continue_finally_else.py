# Repro 9: try-except-finally with continue in except and return in else
data = [1, 'a', 2]
result = []
for item in data:
    try:
        x = int(item)
        result.append(x)
    except ValueError:
        result.append(0)
        continue
    except Exception as e:
        result.append(f'error: {e}')
    finally:
        print(f'item: {item}')
else:
    print(f'result: {result}')
