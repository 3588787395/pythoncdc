def f6(count, reader, limit):
    while count <= limit:
        try:
            for items in reader:
                if len(items) > 0:
                    print(items)
                    continue
                print('empty')
                continue
            break
        except BaseException:
            count += 1
    return count
