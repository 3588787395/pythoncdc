def read_config(path):
    try:
        with open(path) as f:
            data = f.read()
        data
    except FileNotFoundError:
        print('cleanup')
        return ''
    else:
        return print('cleanup')
    finally:
        print('cleanup')
