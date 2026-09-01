# R12 MinRepro 04: for-else-break-return pattern

def find_positive(nums):
    for n in nums:
        if n > 0:
            result = n
            break
    else:
        result = -1
    return result
