def test(f):
    try:
        with open(f) as proc:
            error = proc.read()
            if error:
                l = error.find('x')
                if l != -1:
                    lines = error.split(chr(10))
                    for i in range(len(lines) - 1, -1, -1):
                        if lines[i].find('y') > -1:
                            line_info = lines[i]
                            break
                        continue
                    error = 'processed'
            else:
                error = None
    except BaseException:
        error = 'caught'
    return error
