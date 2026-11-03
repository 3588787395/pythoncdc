def mc12(rows):
    for row in rows:
        match row:
            case [tag, *rest] if rest:
                yield (tag, rest)
            case _:
                yield (tag, [])
