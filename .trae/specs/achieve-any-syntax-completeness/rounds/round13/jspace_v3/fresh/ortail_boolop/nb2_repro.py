def f(name, pat_len):
    if (
            len(name) > pat_len
            and name.startswith(chr(95))
            and name[pat_len:pat_len+1] != [chr(95)]
            and (name[-1] != chr(95) or name[-2] != chr(95))
        ):
        return True
    else:
        return False
