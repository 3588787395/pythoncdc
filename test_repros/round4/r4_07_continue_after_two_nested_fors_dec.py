# Source Generated with Decompyle++ (Python version)
# File: r4_07_continue_after_two_nested_fors.pyc (Python 3.11)

FORBID = ('a', 'b')
BLACK = ('x', 'y')
def f(self, tree, re):
    for node in tree:
        if isinstance(node, int) and isinstance(node.value, str):
            for ca in FORBID:
                if re.search(ca, node.value):
                    return {'e': -1, 'i': ca}
            for ca in BLACK:
                if ca in node.value:
                    return {'e': -1, 'i': ca}
            continue
        if isinstance(node, str) and isinstance(node.func, str):
            return {'e': -1, 'i': 2}
    return {'e': 0, 'i': ''}
