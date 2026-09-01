# Repro 4: try-except-finally with for-else
data = [1, 2, 3]
result = []
for item in data:
    try:
        result.append(item * 2)
    except Exception as e:
        result.append(f'error: {e}')
    finally:
        print(f'item: {item}')
else:
    pass
