"""复现R2-03: if not isinstance展开为if isinstance: pass else:"""
def test_not_isinstance_expand(item):
    if isinstance(item, str):
        pass
    else:
        converted = item
    return converted
