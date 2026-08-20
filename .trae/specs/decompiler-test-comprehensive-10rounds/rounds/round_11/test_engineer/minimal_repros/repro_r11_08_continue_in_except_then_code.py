# Repro 8: try-except with continue in except, then code after try
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
