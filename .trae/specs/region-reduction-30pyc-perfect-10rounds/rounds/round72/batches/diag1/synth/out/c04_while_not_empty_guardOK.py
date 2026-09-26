# Source Generated with Decompyle++ (Python version)
# File: c04_while_not_empty_guard.pyc (Python 3.11)

def sync_worker(queue, lock, stop, handle):
    while not stop:
        if not queue:
            lock.wait(1)
            continue
        handle(queue.pop(0))
    lock.release()
    return None
