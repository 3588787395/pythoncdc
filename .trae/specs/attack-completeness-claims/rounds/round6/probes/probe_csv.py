def main():
    s = 'a,b\n1,2\n3,4\n'
    try:
        print(Sniffer().has_header(s))
    except BaseException as e:
        print('EXC', type(e).__name__, e)
