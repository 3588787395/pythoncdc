def trans_code(lines):
    list1 = []
    flag = True
    line_tmp = []
    left_num_all_tmp = 0
    right_num_all_tmp = 0
    for line in lines:
        left_num = 0
        right_num = 0
        for x in line:
            if x == '(':
                left_num += 1
                continue
            elif x == ')':
                right_num += 1
                continue
        if flag:
            if left_num == right_num:
                list1.append(line)
                flag = True
                continue
            line_tmp.append(line)
            left_num_all_tmp += left_num
            right_num_all_tmp += right_num
            flag = False
            continue
        elif left_num == right_num:
            left_num_all_tmp += left_num
            right_num_all_tmp += right_num
            line_tmp.append(line)
            flag = False
            continue
        else:
            left_num_all_tmp += left_num
            right_num_all_tmp += right_num
            if left_num_all_tmp == right_num_all_tmp:
                line_tmp.append(line)
                new_code = ''
                sum_num = 0
                lenth_line_tmp = len(line_tmp)
                first_flag = True
                for s in line_tmp:
                    if not first_flag:
                        s = s.replace('#', '')
                    sum_num += 1
                    if sum_num != lenth_line_tmp:
                        s = s[:-1]
                        new_code += s
                    else:
                        new_code += s
                list1.append(new_code)
                flag = True
                line_tmp = []
                left_num_all_tmp = 0
                right_num_all_tmp = 0
                continue
            else:
                line_tmp.append(line)
    return list1
