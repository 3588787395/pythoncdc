
def test(error):
    if error:
        l = error.find('x')
        if l != -1:
            error = 'processed'
    else:
        error = None
    return error
