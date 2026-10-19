def s_b69b(a, items):
    if a:
        try:
            items.append(a)
        finally:
            items.reverse()
        return items
    else:
        return []
