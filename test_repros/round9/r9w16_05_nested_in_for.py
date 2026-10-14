def r9w16_05_nested_in_for(items, q, log):
    for item in items:
        while True:
            if len(q) > 0:
                log(item)
            sleep(0.001)
