# R12 MinRepro 02: try-except-else-finally
# Validates else block positioning

def safe_divide(a, b):
    try:
        result = a / b
    except ZeroDivisionError:
        return None
    else:
        return round(result, 2)
    finally:
        print(f'computed {a}/{b}')
