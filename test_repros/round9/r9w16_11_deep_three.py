def r9w16_11_deep_three(groups, q, log):
    while groups:
        for group in groups:
            with opener(group) as handle:
                while True:
                    if len(q) > 0:
                        log(handle.read(q.pop(0)))
                    sleep(0.001)
