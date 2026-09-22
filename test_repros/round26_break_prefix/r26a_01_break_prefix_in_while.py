# R26-A anchor: `if <cond>: <stmt>; break` inside `while True` inside `while`.
# Landed core drops the arm block's leading statement(s) before the break
# (_loop_build_if_with_exit_branches bare Break); witness:
# IQEngine/plugins/plugin_fly_data/__init__.pyc :: _on_before_trading_start_trading_thread
# orig=66 decomp=62, the missing 4 being `order.commit()`.
import time


class Order:
    order_time = 0

    def commit(self):
        return 'committed'


def drain(store):
    while store.items:
        order = store.items.pop(0)
        while True:
            now = time.time()
            if now >= order.order_time:
                order.commit()
                break
            time.sleep(1)
    return store
