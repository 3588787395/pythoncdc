# F-POLARITY (trade_live_broker._sync_worker): worker loop whose first guard is
# an `if not <iterable>` continue-arm nested in a `while not <stop>` loop.  The
# decompiler flips the guard (`POP_JUMP_FORWARD_IF_TRUE to 156` ->
# `POP_JUMP_FORWARD_IF_FALSE to 134`): polarity AND destination both move.
def sync_worker(queue, lock, stop, handle):
    while not stop:
        if not queue:
            lock.wait(1)
            continue
        handle(queue.pop(0))
    lock.release()
    return None
