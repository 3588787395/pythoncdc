# Pattern: if/elif/else with string slicing + `in` tuple membership (mirror amount_trans)
# Function: mirror zt_api.pyc amount_trans full control flow
# Expected: if stock[:2]=='68': nested if/else return; elif stock[:2] in (...): ...; else: ...; return amount
# Actual: same (pyc 100% match, NO-DEFECT control)
def amount_trans(stock, amount):
    if stock[:2] == '68':
        if amount < 200:
            return 0
        else:
            return int(amount)
    elif stock[:2] in ('11', '10', '12'):
        amount = int(amount / 10) * 10
    else:
        amount = int(amount / 100) * 100
    return amount
# NO-DEFECT
