# Source Generated with Decompyle++ (Python version)
# File: r8nop_16_while_cond_body_pass.pyc (Python 3.11)

def n8p16(a, lim, log):
    count = 1
    while True:
        if now() - a <= lim:
            if g(count):
                if count:
                    count += 1
            elif status(count) is STOP:
                break
            else:
                log.error(count)
                continue
        else:
            break
    return count
