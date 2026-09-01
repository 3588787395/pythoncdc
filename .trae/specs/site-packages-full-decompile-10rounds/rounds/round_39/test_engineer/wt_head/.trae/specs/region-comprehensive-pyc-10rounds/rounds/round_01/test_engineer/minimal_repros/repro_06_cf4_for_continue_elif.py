# for loop with continue and elif
def test():
    for i in range(10):
        if i == 3:
            continue
        elif i == 7:
            break
        else:
            print(i)
    return "done"
