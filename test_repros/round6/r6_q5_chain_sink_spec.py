def r6_q5_chain_sink_spec(a, b):
    if a:
        if b:
            work()
            return None
    tail()
