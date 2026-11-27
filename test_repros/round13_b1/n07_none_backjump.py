def walk(node):
    cur = node
    while cur is not None:
        cur = cur.next
    while cur is None:
        cur = cur.sibling
        if cur is not None:
            continue
