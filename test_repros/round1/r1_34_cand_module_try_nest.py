try:
    if __name__ == 'x':
        print('a')
        if __name__ == 'y':
            print('b')
        else:
            print('c')
        print('d')
    else:
        print('e')
except BaseException as exc:
    print(exc)
