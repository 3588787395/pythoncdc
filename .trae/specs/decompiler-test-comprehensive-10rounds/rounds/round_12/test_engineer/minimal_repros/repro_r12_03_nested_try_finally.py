# R12 MinRepro 03: nested try-finally

def nested(file_path):
    try:
        try:
            f = open(file_path)
            data = f.read()
        finally:
            f.close()
    except FileNotFoundError:
        data = ''
    return data
