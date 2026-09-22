# Independent defect found while writing Round 29 G0 (NOT fixed by R29-A).
# MEASURED: <module> 142/138 with jump_diffs=2, true_diffs=122 under the pre-landing
# landed core AND identically under R29-A -- a genuine 4-instruction deficit in a
# module-level if/else + for + nested if/elif shape. Hand-off material for a later round.

bsuccess = False
index_codes = []
standard_index = 3
payload = []


def _probe(flag, rows):
    return 'probe=%s/%s' % (flag, rows)


# ---------------------------------------------------------------- diagnostic 1
if bsuccess or not index_codes:
    total = 0
    for row in (payload or [1, 2]):
        if row == 1:
            print('one')
        else:
            if row > 9:
                print('big')
            elif row:
                print('small')
                total = total + row
        print('final row:', row)
        total = total + 1
    eshare = _probe(True, total)
    bsuccess = True
else:
    print('ERROR: nothing to do')
print('++++++ end of run ++++++ : %s' % bsuccess)


# ---------------------------------------------------------------- diagnostic 2
count = 0
if bsuccess:
    for item in payload:
        if item:
            count = count + 1
        else:
            count = count - 1
        print('item done')
    eshare = _probe(bsuccess, count)
else:
    print('ERROR: skipped')
print('++++++ end two ++++++ : %s' % eshare)


# ---------------------------------------------------------------- control 1
def r29a_ctl_plain_if_else(flag):
    if flag:
        a = 1
    else:
        a = 2
    return a


# ---------------------------------------------------------------- control 2
def r29a_ctl_arm_ends_in_sink(flag):
    if flag:
        return True
    print('post-if')
    return False


# ---------------------------------------------------------------- control 3
def r29a_ctl_nested_join(flag, rows):
    total = 0
    if flag:
        for row in rows:
            if row:
                total = total + row
            else:
                total = total - row
            print('row')
        bsuccess = True
    else:
        print('ERROR')
    print('end : %s' % total)
    return total
