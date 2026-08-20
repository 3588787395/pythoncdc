# R12 MinRepro 06: with + try-finally

def read_config(path):
    try:
        with open(path) as f:
            data = f.read()
        return data
    except FileNotFoundError:
        return ''
    finally:
        print('cleanup')
