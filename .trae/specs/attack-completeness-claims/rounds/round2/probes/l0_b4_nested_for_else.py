"""AT-04: 内外双层 for-else（B109 nested_loop_else 形态）"""


def b4(xs):
    for a in xs:
        for b in xs:
            print(a, b)
        else:
            print('inner-else')
    else:
        print('outer-else')
