# rv_04 修复一 B 臂（or-run 续接类）嵌套变体 2：
# or 先行混合链 `if b or c and a:`（触发 _b1b_loop_body_run_continuation
# 的 or-run 续接判据），位于双层 for 体内（for > for > if）


def f(grid, a, b, c):
    hits = 0
    for row in grid:
        for cell in row:
            if b or c and a:
                hits += 1
                continue
    return hits
