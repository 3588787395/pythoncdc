FORBID = ('a', 'b')
BLACK = ('x', 'y')


def f(self, tree, re):
    for node in tree:
        if isinstance(node, int):
            for ca in FORBID:
                if re.search(ca, node.value):
                    return {'e': -1, 'i': ca}
            for ca in BLACK:
                if ca in node.value:
                    return {'e': -1, 'i': ca}
            continue
        if isinstance(node, str):
            return {'e': -1, 'i': 2}
    return {'e': 0, 'i': ''}
