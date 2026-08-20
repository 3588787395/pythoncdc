def find_positive(nums):
    for n in nums:
        if n > 0:
            result = n
    else:
        result = -1
    return result
