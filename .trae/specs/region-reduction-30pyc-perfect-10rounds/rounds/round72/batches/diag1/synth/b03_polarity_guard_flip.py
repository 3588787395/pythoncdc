# F-POLARITY (trade_live_broker._sync_worker / quote get_history): the decompiler
# flips the branch sense of a guard (`if X` -> `if not X`) while keeping the same
# jump destination, so the first divergent instruction is
# POP_JUMP_FORWARD_IF_TRUE <-> POP_JUMP_FORWARD_IF_FALSE.
def get_history(code, count, direction):
    if not code:
        return None
    if count <= 0:
        count = 50
    return fetch(code, count, direction)


def sync_worker(items, lock, stop):
    while not stop:
        if not items:
            lock.wait(1)
            continue
        handle(items.pop(0))
    return None
