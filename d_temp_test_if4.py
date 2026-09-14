
def test(error):
    if error:
        l = error.find('x')
        if l != -1:
            error = 'processed'
        else:
            pass
    else:
        error = None
    return error
