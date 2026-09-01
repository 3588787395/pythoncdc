# Repro 3: nested try-except with continue in inner except and finally
data = [1, 'a', -5, 200]
result = []
for item in data:
    try:
        if isinstance(item, str):
            try:
                converted = int(item)
                result.append(converted)
            except ValueError:
                result.append(f'string convert error: {item}')
                continue
        else:
            converted = item
        print(f'processing: {item}')
        try:
            if converted > 100:
                result.append(converted // 10)
            elif converted < 0:
                result.append(abs(converted))
            else:
                result.append(converted * 2)
        except Exception as e:
            result.append(f'value error: {e}')
    except Exception as e:
        result.append(f'outer error: {e}')
    finally:
        print(f'done: {item}')
