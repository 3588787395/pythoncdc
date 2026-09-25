"""Round 64 batch diag5 witness W-M1: continue-sink merge refusal.

Mirrors site-packages/IQEngine/plugins/plugin_system_matcher/matcher.pyc
:: DefaultMatcher.match (source 211..219 with the post-chain sibling at 292).

Shape under test (inside a `for` body, inside an outer `if` that has an `elif`):

    if it.kind not in (...):          # outer arm A
        if <c1>:                      # then arm is a BARE `continue`
            continue
        if <c2>:                      # <- this block is `else_succ` of the if above
            ...
        <loop-tail siblings>          # must stay in the loop body, after the if

Landed site: core/cfg/region_analyzer.py:17063-17079 (continue-sink merge rule).
`_find_nearest_common_post_dominator(then, else)` returns the loop header, and the
rule would re-aim merge := else_succ -- but its last conjunct `if not _elif:`
refuses, because else_succ has 2 conditional successors and ends in a forward
conditional jump, i.e. it "looks like an elif condition block".  With merge stuck
on the loop header, `_collect_branch_blocks` bounds the else arm by nothing, so the
loop-tail siblings are absorbed into the arm of the `if <c1>` statement: the whole
run is emitted after the statements that follow the outer if.

With a bare-continue then arm the ambiguity the `_elif` guard protects is empty:
`elif` and a sibling `if` compile to identical control flow, because the then arm
never falls through into else_succ.

Candidate under test: specs/cand_r64d5_contbare2.json -- treat the then arm as bare
when, after NOP/CACHE/PRECALL/EXTENDED_ARG/RESUME, it holds nothing but the back
edge, and re-aim merge := else_succ in that shape (merge must be the loop header).

Run from D:/Temp/opencode/r64gate/diag5:
  python -X utf8 h62.py run --arm=landed --list=w_m1.txt --out=dump/wm_landed.jsonl
  python -X utf8 h62.py run --arm=cA2    --list=w_m1.txt --out=dump/wm_cA2.jsonl
"""


def probe(items, price_limit, volume_limit, ratio, log):
    total = 0
    for it in items:
        if price_limit:
            if it.kind not in ('a', 'b', 'c'):
                if it.direction == 'buy' and it.price >= ratio:
                    continue
                if it.direction == 'sell' and it.price <= ratio:
                    continue
                if volume_limit:
                    bar = it.value
                    if bar <= 0:
                        log.warning('bad bar %s' % it.symbol)
                        continue
                    fill = round(bar * ratio)
                    if fill <= 0:
                        log.warning('empty fill %s' % it.symbol)
                        continue
                    total += fill
                    log.info('filled %s %s' % (it.symbol, fill))
                else:
                    total += it.value
                total = total + 1
            elif it.kind == 'a':
                total += 2
            else:
                total += 3
        else:
            total += 4
    return total
