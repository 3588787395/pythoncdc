def trans_code(lines):
    result = []
    flag = True
    for line in lines:
        left = 0
        right = 0
        for x in line:
            if x == '(':
                left += 1
                continue
            elif x == ')':
                right += 1
                continue
        if flag:
            if left == right:
                result.append(line)
                flag = True
                continue
            flag = False
            continue
        elif left == right:
            flag = False
            continue
        else:
            if left == right:
                result.append(line)
    return result
