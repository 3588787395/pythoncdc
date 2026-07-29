
def f(items, data_out):
    for i in items:
        for key, value in i.items():
            if not key == 'skip':
                if key == 'a':
                    continue
                else:
                    pass
                    continue
        else:
            data_out.append(1)
