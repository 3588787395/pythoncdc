def main():
    try:
        print(SequenceMatcher(None, 'abcd', 'bcde').get_matching_blocks())
    except BaseException as e:
        print('EXC', type(e).__name__, e)
