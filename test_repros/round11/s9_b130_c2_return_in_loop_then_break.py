def f10(count, reader, limit):
    while count <= limit:
        try:
            for items in reader:
                if len(items) > 0:
                    if items[0] == 1:
                        return items
                    else:
                        return items[2]
                    continue
                print('empty')
                continue
            break
        except BaseException:
            count += 1
    return count
