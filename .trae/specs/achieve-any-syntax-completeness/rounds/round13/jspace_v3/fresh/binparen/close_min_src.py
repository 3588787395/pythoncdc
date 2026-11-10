def write_pad(fileobj, NUL, BLOCKSIZE):
    fileobj.write(NUL * (BLOCKSIZE * 2))
    fileobj.write(NUL * (BLOCKSIZE * 3))
