def safe_divide(a, b):
    try:
        result = a / b
    except ZeroDivisionError:
        print(f'computed {a}/{b}')
    else:
        round(result, 2)
        return print(f'computed {a}/{b}')
    finally:
        print(f'computed {a}/{b}')
