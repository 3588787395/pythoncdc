while True:
    if not is_active():
        continue
    if not is_ready():
        continue
    execute()
