def f(name, pat_len):
    return (
        len(name) > pat_len
        and name.startswith(chr(95))
        and name[pat_len:pat_len+1] != [chr(95)]
        and (name[-1] != chr(95) or name[-2] != chr(95))
    )
