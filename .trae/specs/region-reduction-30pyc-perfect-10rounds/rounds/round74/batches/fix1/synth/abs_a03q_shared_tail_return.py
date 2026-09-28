# synth a03q -- merged child holds trailing statement (shape from
# fly/data/quote.pyc::get_real_from_zeromq flag ladder).
# expected: landed / abs1 inline `return None` into each branch and drop the
# shared `return None, flag` tail; absj emits the merged child -> tail kept.
def synth_a03q_shared_tail_return(redata, flag, log):
    if not redata:
        if flag == 1:
            log.info('real数据转化异常，默认返回空值')
        elif flag == -1:
            log.info('real数据返回空值')
        return None, flag
    return redata
