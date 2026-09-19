def f(self, tree):
    for node in tree:
        if isinstance(node, int) and isinstance(node.value, str):
            continue
        if isinstance(node, str):
            return 2
    return 0
