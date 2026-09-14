
def test(f):
    with open(f) as proc:
        error = proc.read()
        if error:
            l = error.find('x')
            if l != -1:
                error = 'processed'
        else:
            error = None
    return error
