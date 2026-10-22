# Source Generated with Decompyle++ (Python version)
# File: sp_anyio_fileio.pyc (Python 3.11)

from __future__ import annotations
import os
import pathlib
import sys
from collections.abc import AsyncIterator, Callable, Iterable, Iterator, Sequence
from dataclasses import dataclass
from functools import partial
from os import PathLike
from typing import IO, TYPE_CHECKING, Any, AnyStr, ClassVar, Final, Generic, overload
from .. import to_thread
from ..abc import AsyncResource
if TYPE_CHECKING:
    from types import ModuleType
    from _typeshed import OpenBinaryMode, OpenTextMode, ReadableBuffer, WriteableBuffer
else:
    ReadableBuffer = OpenBinaryMode = OpenTextMode = WriteableBuffer = object
class AsyncFile(AsyncResource, Generic[AnyStr]):
    __doc__ = """
    An asynchronous file object.

    This class wraps a standard file object and provides async friendly versions of the
    following blocking methods (where available on the original file object):

    * read
    * read1
    * readline
    * readlines
    * readinto
    * readinto1
    * write
    * writelines
    * truncate
    * seek
    * tell
    * flush

    All other methods are directly passed through.

    This class supports the asynchronous context manager protocol which closes the
    underlying file at the end of the context block.

    This class also supports asynchronous iteration::

        async with await open_file(...) as f:
            async for line in f:
                print(line)
    """
    def __init__(self, fp):
        self._fp = fp
    def __getattr__(self, name):
        return getattr(self._fp, name)
    @property
    def wrapped(self):
        """The wrapped file object."""
        return self._fp
    async def __aiter__(self):
        while True:
            if await self.readline():
                yield line
            else:
                break
    async def aclose(self):
        return await to_thread.run_sync(self._fp.close)
    async def read(self, size=-1):
        return await to_thread.run_sync(self._fp.read, size)
    async def read1(self, size=-1):
        return await to_thread.run_sync(self._fp.read1, size)
    async def readline(self):
        return await to_thread.run_sync(self._fp.readline)
    async def readlines(self):
        return await to_thread.run_sync(self._fp.readlines)
    async def readinto(self, b):
        return await to_thread.run_sync(self._fp.readinto, b)
    async def readinto1(self, b):
        return await to_thread.run_sync(self._fp.readinto1, b)
    @overload
    async def write(self, b):
        return None
    @overload
    async def write(self, b):
        return None
    async def write(self, b):
        return await to_thread.run_sync(self._fp.write, b)
    @overload
    async def writelines(self, lines):
        return None
    @overload
    async def writelines(self, lines):
        return None
    async def writelines(self, lines):
        return await to_thread.run_sync(self._fp.writelines, lines)
    async def truncate(self, size=None):
        return await to_thread.run_sync(self._fp.truncate, size)
    async def seek(self, offset, whence=os.SEEK_SET):
        return await to_thread.run_sync(self._fp.seek, offset, whence)
    async def tell(self):
        return await to_thread.run_sync(self._fp.tell)
    async def flush(self):
        return await to_thread.run_sync(self._fp.flush)
@overload
async def open_file(file, mode, buffering=None, encoding=None, errors=None, newline=None, closefd=None, opener=None):
    return None
@overload
async def open_file(file, mode=None, buffering=None, encoding=None, errors=None, newline=None, closefd=None, opener=None):
    return None
async def open_file(file, mode='r', buffering=-1, encoding=None, errors=None, newline=None, closefd=True, opener=None):
    """
    Open a file asynchronously.

    The arguments are exactly the same as for the builtin :func:`open`.

    :return: an asynchronous file object

    """
    fp = await to_thread.run_sync(open, file, mode, buffering, encoding, errors, newline, closefd, opener)
    return AsyncFile(fp)
def wrap_file(file):
    """
    Wrap an existing file as an asynchronous file.

    :param file: an existing file-like object
    :return: an asynchronous file object

    """
    return AsyncFile(file)
@dataclass(eq=False)
class _PathIterator(AsyncIterator['Path']):
    iterator: 'Iterator[PathLike[str]]'
    async def __anext__(self):
        if await to_thread.run_sync(next, self.iterator, None, abandon_on_cancel=True):
            raise StopAsyncIteration from None
        return Path(nextval)
class Path:
    __doc__ = """
    An asynchronous version of :class:`pathlib.Path`.

    This class cannot be substituted for :class:`pathlib.Path` or
    :class:`pathlib.PurePath`, but it is compatible with the :class:`os.PathLike`
    interface.

    It implements the Python 3.10 version of :class:`pathlib.Path` interface, except for
    the deprecated :meth:`~pathlib.Path.link_to` method.

    Some methods may be unavailable or have limited functionality, based on the Python
    version:

    * :meth:`~pathlib.Path.copy` (available on Python 3.14 or later)
    * :meth:`~pathlib.Path.copy_into` (available on Python 3.14 or later)
    * :meth:`~pathlib.Path.from_uri` (available on Python 3.13 or later)
    * :meth:`~pathlib.PurePath.full_match` (available on Python 3.13 or later)
    * :attr:`~pathlib.Path.info` (available on Python 3.14 or later)
    * :meth:`~pathlib.Path.is_junction` (available on Python 3.12 or later)
    * :meth:`~pathlib.PurePath.match` (the ``case_sensitive`` parameter is only
      available on Python 3.13 or later)
    * :meth:`~pathlib.Path.move` (available on Python 3.14 or later)
    * :meth:`~pathlib.Path.move_into` (available on Python 3.14 or later)
    * :meth:`~pathlib.PurePath.relative_to` (the ``walk_up`` parameter is only available
      on Python 3.12 or later)
    * :meth:`~pathlib.Path.walk` (available on Python 3.12 or later)

    Any methods that do disk I/O need to be awaited on. These methods are:

    * :meth:`~pathlib.Path.absolute`
    * :meth:`~pathlib.Path.chmod`
    * :meth:`~pathlib.Path.cwd`
    * :meth:`~pathlib.Path.exists`
    * :meth:`~pathlib.Path.expanduser`
    * :meth:`~pathlib.Path.group`
    * :meth:`~pathlib.Path.hardlink_to`
    * :meth:`~pathlib.Path.home`
    * :meth:`~pathlib.Path.is_block_device`
    * :meth:`~pathlib.Path.is_char_device`
    * :meth:`~pathlib.Path.is_dir`
    * :meth:`~pathlib.Path.is_fifo`
    * :meth:`~pathlib.Path.is_file`
    * :meth:`~pathlib.Path.is_junction`
    * :meth:`~pathlib.Path.is_mount`
    * :meth:`~pathlib.Path.is_socket`
    * :meth:`~pathlib.Path.is_symlink`
    * :meth:`~pathlib.Path.lchmod`
    * :meth:`~pathlib.Path.lstat`
    * :meth:`~pathlib.Path.mkdir`
    * :meth:`~pathlib.Path.open`
    * :meth:`~pathlib.Path.owner`
    * :meth:`~pathlib.Path.read_bytes`
    * :meth:`~pathlib.Path.read_text`
    * :meth:`~pathlib.Path.readlink`
    * :meth:`~pathlib.Path.rename`
    * :meth:`~pathlib.Path.replace`
    * :meth:`~pathlib.Path.resolve`
    * :meth:`~pathlib.Path.rmdir`
    * :meth:`~pathlib.Path.samefile`
    * :meth:`~pathlib.Path.stat`
    * :meth:`~pathlib.Path.symlink_to`
    * :meth:`~pathlib.Path.touch`
    * :meth:`~pathlib.Path.unlink`
    * :meth:`~pathlib.Path.walk`
    * :meth:`~pathlib.Path.write_bytes`
    * :meth:`~pathlib.Path.write_text`

    Additionally, the following methods return an async iterator yielding
    :class:`~.Path` objects:

    * :meth:`~pathlib.Path.glob`
    * :meth:`~pathlib.Path.iterdir`
    * :meth:`~pathlib.Path.rglob`
    """
    __slots__ = ('_path', '__weakref__')
    __annotations__['__weakref__'] = 'Any'
    def __init__(self, *args):
        self._path = pathlib.Path(*args)
    def __fspath__(self):
        return self._path.__fspath__()
    if sys.version_info >= (3, 15):
        def __vfspath__(self):
            return self._path.__vfspath__()
    def __str__(self):
        return self._path.__str__()
    def __repr__(self):
        return f'{self.__class__.__name__}({self.as_posix()!r})'
    def __bytes__(self):
        return self._path.__bytes__()
    def __hash__(self):
        return self._path.__hash__()
    def __eq__(self, other):
        target = other._path if isinstance(other, Path) else other
        return self._path.__eq__(target)
    def __lt__(self, other):
        target = other._path if isinstance(other, Path) else other
        return self._path.__lt__(target)
    def __le__(self, other):
        target = other._path if isinstance(other, Path) else other
        return self._path.__le__(target)
    def __gt__(self, other):
        target = other._path if isinstance(other, Path) else other
        return self._path.__gt__(target)
    def __ge__(self, other):
        target = other._path if isinstance(other, Path) else other
        return self._path.__ge__(target)
    def __truediv__(self, other):
        return Path(self._path / other)
    def __rtruediv__(self, other):
        return Path(other) / self
    @property
    def parts(self):
        return self._path.parts
    @property
    def drive(self):
        return self._path.drive
    @property
    def root(self):
        return self._path.root
    @property
    def anchor(self):
        return self._path.anchor
    @property
    def parents(self):
        return tuple((Path(p) for p in self._path.parents))
    @property
    def parent(self):
        return Path(self._path.parent)
    @property
    def name(self):
        return self._path.name
    @property
    def suffix(self):
        return self._path.suffix
    @property
    def suffixes(self):
        return self._path.suffixes
    @property
    def stem(self):
        return self._path.stem
    async def absolute(self):
        path = await to_thread.run_sync(self._path.absolute)
        return Path(path)
    def as_posix(self):
        return self._path.as_posix()
    def as_uri(self):
        return self._path.as_uri()
    if sys.version_info >= (3, 13):
        parser: 'ClassVar[ModuleType]' = pathlib.Path.parser
        @classmethod
        def from_uri(cls, uri):
            return Path(pathlib.Path.from_uri(uri))
        def full_match(self, path_pattern, *, case_sensitive=None):
            return self._path.full_match(path_pattern, case_sensitive=case_sensitive)
        def match(self, path_pattern, *, case_sensitive=None):
            return self._path.match(path_pattern, case_sensitive=case_sensitive)
    else:
        def match(self, path_pattern):
            return self._path.match(path_pattern)
    if sys.version_info >= (3, 14):
        @property
        def info(self):
            return self._path.info
        async def copy(self, target, *, follow_symlinks=True, preserve_metadata=False):
            func = partial(self._path.copy, follow_symlinks=follow_symlinks, preserve_metadata=preserve_metadata)
            return Path(await to_thread.run_sync(func, pathlib.Path(target)))
        async def copy_into(self, target_dir, *, follow_symlinks=True, preserve_metadata=False):
            func = partial(self._path.copy_into, follow_symlinks=follow_symlinks, preserve_metadata=preserve_metadata)
            return Path(await to_thread.run_sync(func, pathlib.Path(target_dir)))
        async def move(self, target):
            target = pathlib.Path(target)
            return Path(await to_thread.run_sync(self._path.move, target))
        async def move_into(self, target_dir):
            return Path(await to_thread.run_sync(self._path.move_into, target_dir))
    def is_relative_to(self, other):
        try:
            self.relative_to(other)
            return True
        except ValueError:
            return False
    async def chmod(self, mode, *, follow_symlinks=True):
        func = partial(os.chmod, follow_symlinks=follow_symlinks)
        return await to_thread.run_sync(func, self._path, mode)
    @classmethod
    async def cwd(cls):
        path = await to_thread.run_sync(pathlib.Path.cwd)
        return cls(path)
    async def exists(self):
        return await to_thread.run_sync(self._path.exists, abandon_on_cancel=True)
    async def expanduser(self):
        return Path(await to_thread.run_sync(self._path.expanduser, abandon_on_cancel=True))
    if sys.version_info < (3, 12):
        def glob(self, pattern):
            gen = self._path.glob(pattern)
            return _PathIterator(gen)
    elif (3, 12) <= sys.version_info < (3, 13):
        def glob(self, pattern, *, case_sensitive=None):
            gen = self._path.glob(pattern, case_sensitive=case_sensitive)
            return _PathIterator(gen)
        def glob(self, pattern, *, case_sensitive=None, recurse_symlinks=False):
            gen = self._path.glob(pattern, case_sensitive=case_sensitive, recurse_symlinks=recurse_symlinks)
            return _PathIterator(gen)
    elif sys.version_info >= (3, 13):
        pass
    async def group(self):
        return await to_thread.run_sync(self._path.group, abandon_on_cancel=True)
    async def hardlink_to(self, target):
        if isinstance(target, Path):
            target = target._path
        await to_thread.run_sync(os.link, target, self)
    @classmethod
    async def home(cls):
        home_path = await to_thread.run_sync(pathlib.Path.home)
        return cls(home_path)
    def is_absolute(self):
        return self._path.is_absolute()
    async def is_block_device(self):
        return await to_thread.run_sync(self._path.is_block_device, abandon_on_cancel=True)
    async def is_char_device(self):
        return await to_thread.run_sync(self._path.is_char_device, abandon_on_cancel=True)
    async def is_dir(self):
        return await to_thread.run_sync(self._path.is_dir, abandon_on_cancel=True)
    async def is_fifo(self):
        return await to_thread.run_sync(self._path.is_fifo, abandon_on_cancel=True)
    async def is_file(self):
        return await to_thread.run_sync(self._path.is_file, abandon_on_cancel=True)
    if sys.version_info >= (3, 12):
        async def is_junction(self):
            return await to_thread.run_sync(self._path.is_junction)
    async def is_mount(self):
        return await to_thread.run_sync(os.path.ismount, self._path, abandon_on_cancel=True)
    if sys.version_info < (3, 15):
        def is_reserved(self):
            return self._path.is_reserved()
    async def is_socket(self):
        return await to_thread.run_sync(self._path.is_socket, abandon_on_cancel=True)
    async def is_symlink(self):
        return await to_thread.run_sync(self._path.is_symlink, abandon_on_cancel=True)
    async def iterdir(self):
        gen = self._path.iterdir() if sys.version_info < (3, 13) else _PathIterator(gen)
        async for path in _PathIterator(gen):
            yield path
    def joinpath(self, *args):
        return Path(self._path.joinpath(*args))
    async def lchmod(self, mode):
        await to_thread.run_sync(self._path.lchmod, mode)
    async def lstat(self):
        return await to_thread.run_sync(self._path.lstat, abandon_on_cancel=True)
    async def mkdir(self, mode=511, parents=False, exist_ok=False):
        await to_thread.run_sync(self._path.mkdir, mode, parents, exist_ok)
    @overload
    async def open(self, mode, buffering=None, encoding=None, errors=None, newline=None):
        return None
    @overload
    async def open(self, mode=None, buffering=None, encoding=None, errors=None, newline=None):
        return None
    async def open(self, mode='r', buffering=-1, encoding=None, errors=None, newline=None):
        fp = await to_thread.run_sync(self._path.open, mode, buffering, encoding, errors, newline)
        return AsyncFile(fp)
    async def owner(self):
        return await to_thread.run_sync(self._path.owner, abandon_on_cancel=True)
    async def read_bytes(self):
        return await to_thread.run_sync(self._path.read_bytes)
    async def read_text(self, encoding=None, errors=None):
        return await to_thread.run_sync(self._path.read_text, encoding, errors)
    if sys.version_info >= (3, 12):
        def relative_to(self, *other, walk_up=False):
            others = [pathlib.Path(other) for other in other]
            return Path(self._path.relative_to(*others, walk_up=walk_up))
    else:
        def relative_to(self, *other):
            return Path(self._path.relative_to(*other))
    async def readlink(self):
        target = await to_thread.run_sync(os.readlink, self._path)
        return Path(target)
    async def rename(self, target):
        if isinstance(target, Path):
            target = target._path
        await to_thread.run_sync(self._path.rename, target)
        return Path(target)
    async def replace(self, target):
        if isinstance(target, Path):
            target = target._path
        await to_thread.run_sync(self._path.replace, target)
        return Path(target)
    async def resolve(self, strict=False):
        func = partial(self._path.resolve, strict=strict)
        return Path(await to_thread.run_sync(func, abandon_on_cancel=True))
    if sys.version_info < (3, 12):
        def rglob(self, pattern):
            gen = self._path.rglob(pattern)
            return _PathIterator(gen)
    elif (3, 12) <= sys.version_info < (3, 13):
        def rglob(self, pattern, *, case_sensitive=None):
            gen = self._path.rglob(pattern, case_sensitive=case_sensitive)
            return _PathIterator(gen)
        def rglob(self, pattern, *, case_sensitive=None, recurse_symlinks=False):
            gen = self._path.rglob(pattern, case_sensitive=case_sensitive, recurse_symlinks=recurse_symlinks)
            return _PathIterator(gen)
    elif sys.version_info >= (3, 13):
        pass
    async def rmdir(self):
        await to_thread.run_sync(self._path.rmdir)
    async def samefile(self, other_path):
        if isinstance(other_path, Path):
            other_path = other_path._path
        return await to_thread.run_sync(self._path.samefile, other_path, abandon_on_cancel=True)
    async def stat(self, *, follow_symlinks=True):
        func = partial(os.stat, follow_symlinks=follow_symlinks)
        return await to_thread.run_sync(func, self._path, abandon_on_cancel=True)
    async def symlink_to(self, target, target_is_directory=False):
        if isinstance(target, Path):
            target = target._path
        await to_thread.run_sync(self._path.symlink_to, target, target_is_directory)
    async def touch(self, mode=438, exist_ok=True):
        await to_thread.run_sync(self._path.touch, mode, exist_ok)
    async def unlink(self, missing_ok=False):
        try:
            await to_thread.run_sync(self._path.unlink)
            return None
        except FileNotFoundError:
            if not missing_ok:
                raise
            return None
    if sys.version_info >= (3, 12):
        async def walk(self, top_down=True, on_error=None, follow_symlinks=False):
            def get_next_value():
                try:
                    return next(gen)
                except StopIteration:
                    return None
            gen = self._path.walk(top_down, on_error, follow_symlinks)
            while True:
                if await to_thread.run_sync(get_next_value):
                    break
                root, dirs, paths = value
                yield (Path(root), dirs, paths)
    def with_name(self, name):
        return Path(self._path.with_name(name))
    def with_stem(self, stem):
        return Path(self._path.with_name(stem + self._path.suffix))
    def with_suffix(self, suffix):
        return Path(self._path.with_suffix(suffix))
    def with_segments(self, *pathsegments):
        return Path(*pathsegments)
    async def write_bytes(self, data):
        return await to_thread.run_sync(self._path.write_bytes, data)
    async def write_text(self, data, encoding=None, errors=None, newline=None):
        return await to_thread.run_sync(self._path.write_text, data, encoding, errors, newline)
PathLike.register(Path)
