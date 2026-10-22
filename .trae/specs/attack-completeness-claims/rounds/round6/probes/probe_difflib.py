def main():
    try:
        print(SequenceMatcher(None, 'abcd', 'bcde').ratio())
    except BaseException as e:
        print('EXC', type(e).__name__, e)
