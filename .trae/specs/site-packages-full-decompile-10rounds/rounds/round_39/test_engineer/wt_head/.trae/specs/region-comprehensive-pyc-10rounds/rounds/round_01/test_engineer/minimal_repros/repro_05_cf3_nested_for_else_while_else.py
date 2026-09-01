# Nested for-else + while-else
def test():
    for item in [1, 2, 3]:
        if item == 2:
            break
    else:
        print("for else")
        counter = 0
        while counter < 5:
            if counter == 3:
                break
            counter += 1
        else:
            print("while else")
    return "done"
