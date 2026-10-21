# Source Generated with Decompyle++ (Python version)
# File: l0_b4_nested_for_else.pyc (Python 3.11)

__doc__ = 'AT-04: 内外双层 for-else（B109 nested_loop_else 形态）'
def b4(xs):
    for a in xs:
        for b in xs:
            print(a, b)
        print('inner-else')
    print('outer-else')
