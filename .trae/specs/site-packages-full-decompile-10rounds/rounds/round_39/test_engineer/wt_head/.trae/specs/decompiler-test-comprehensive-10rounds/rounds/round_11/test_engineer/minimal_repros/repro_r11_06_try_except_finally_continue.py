# Repro 6: try-except-finally in for loop, continue in except, print in finally
data = [1, 'a', 2]
for item in data:
    try:
        x = int(item)
    except ValueError:
        print(f'error: {item}')
        continue
    finally:
        print(f'done: {item}')
