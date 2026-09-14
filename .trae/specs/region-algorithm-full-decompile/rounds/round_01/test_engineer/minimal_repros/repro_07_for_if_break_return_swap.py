def find_item(items, key):
    for item in items:
        if item[0] == key:
            if len(item) > 5:
                return item
            break
    return None
