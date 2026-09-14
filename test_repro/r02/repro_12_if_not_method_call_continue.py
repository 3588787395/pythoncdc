while True:
    if not is_future_tradetime(dt_strf):
        continue
    queue.put(item)
    time.sleep(3)
