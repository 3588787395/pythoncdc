while True:
    if not data_proxy.is_available(source):
        continue
    result = data_proxy.fetch()
