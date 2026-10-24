# Source Generated with Decompyle++ (Python version)
# File: streams.cpython-311.pyc (Python 3.11)

__all__ = ('StreamReader', 'StreamWriter', 'StreamReaderProtocol', 'open_connection', 'start_server')
import collections
import socket
import sys
import warnings
import weakref
if hasattr(socket, 'AF_UNIX'):
    __all__ += ('open_unix_connection', 'start_unix_server')
from . import coroutines
from . import events
from . import exceptions
from . import format_helpers
from . import protocols
from .log import logger
from .tasks import sleep
_DEFAULT_LIMIT = 65536
async def open_connection(host=None, port=None, *, limit=_DEFAULT_LIMIT, **kwds):
    """A wrapper for create_connection() returning a (reader, writer) pair.

    The reader returned is a StreamReader instance; the writer is a
    StreamWriter instance.

    The arguments are all the usual arguments to create_connection()
    except protocol_factory; most common are positional host and port,
    with various optional keyword arguments following.

    Additional optional keyword arguments are loop (to set the event loop
    instance to use) and limit (to set the buffer limit passed to the
    StreamReader).

    (If you want to customize the StreamReader and/or
    StreamReaderProtocol classes, just copy the code -- there's
    really nothing special here except some convenience.)
    """
    loop = events.get_running_loop()
    reader = StreamReader(limit=limit, loop=loop)
    protocol = StreamReaderProtocol(reader, loop=loop)
    transport, _ = await loop.create_connection(lambda : protocol, host, port, **(kwds))
    writer = StreamWriter(transport, protocol, reader, loop)
    return (reader, writer)
async def start_server(client_connected_cb, host=None, port=None, *, limit=_DEFAULT_LIMIT, **kwds):
    """Start a socket server, call back for each client connected.

    The first parameter, `client_connected_cb`, takes two parameters:
    client_reader, client_writer.  client_reader is a StreamReader
    object, while client_writer is a StreamWriter object.  This
    parameter can either be a plain callback function or a coroutine;
    if it is a coroutine, it will be automatically converted into a
    Task.

    The rest of the arguments are all the usual arguments to
    loop.create_server() except protocol_factory; most common are
    positional host and port, with various optional keyword arguments
    following.  The return value is the same as loop.create_server().

    Additional optional keyword argument is limit (to set the buffer
    limit passed to the StreamReader).

    The return value is the same as loop.create_server(), i.e. a
    Server object which can be used to stop the service.
    """
    loop = events.get_running_loop()
    def factory():
        reader = StreamReader(limit=limit, loop=loop)
        protocol = StreamReaderProtocol(reader, client_connected_cb, loop=loop)
        return protocol
    return await loop.create_server(factory, host, port, **(kwds))
if hasattr(socket, 'AF_UNIX'):
    async def open_unix_connection(path=None, *, limit=_DEFAULT_LIMIT, **kwds):
        """Similar to `open_connection` but works with UNIX Domain Sockets."""
        loop = events.get_running_loop()
        reader = StreamReader(limit=limit, loop=loop)
        protocol = StreamReaderProtocol(reader, loop=loop)
        transport, _ = await loop.create_unix_connection(lambda : protocol, path, **(kwds))
        writer = StreamWriter(transport, protocol, reader, loop)
        return (reader, writer)
    async def start_unix_server(client_connected_cb, path=None, *, limit=_DEFAULT_LIMIT, **kwds):
        """Similar to `start_server` but works with UNIX Domain Sockets."""
        loop = events.get_running_loop()
        def factory():
            reader = StreamReader(limit=limit, loop=loop)
            protocol = StreamReaderProtocol(reader, client_connected_cb, loop=loop)
            return protocol
        return await loop.create_unix_server(factory, path, **(kwds))
class FlowControlMixin(protocols.Protocol):
    __doc__ = """Reusable flow control logic for StreamWriter.drain().

    This implements the protocol methods pause_writing(),
    resume_writing() and connection_lost().  If the subclass overrides
    these it must call the super methods.

    StreamWriter.drain() must wait for _drain_helper() coroutine.
    """
    def __init__(self, loop=None):
        if loop is None:
            self._loop = events._get_event_loop(stacklevel=4)
        else:
            self._loop = loop
        self._paused = False
        self._drain_waiters = collections.deque()
        self._connection_lost = False
    def pause_writing(self):
        assert self._paused
        self._paused = True
        if self._loop.get_debug():
            logger.debug('%r pauses writing', self)
            return None
        else:
            return None
    def resume_writing(self):
        assert self._paused
        self._paused = False
        if self._loop.get_debug():
            logger.debug('%r resumes writing', self)
        for waiter in self._drain_waiters:
            if not waiter.done():
                waiter.set_result(None)
    def connection_lost(self, exc):
        self._connection_lost = True
        if not self._paused:
            return None
        else:
            for waiter in self._drain_waiters:
                if not waiter.done():
                    if exc is None:
                        waiter.set_result(None)
                        continue
                    waiter.set_exception(exc)
    async def _drain_helper(self):
        if self._connection_lost:
            raise ConnectionResetError('Connection lost')
        if not self._paused:
            return None
        waiter = self._loop.create_future()
        self._drain_waiters.append(waiter)
        try:
            await waiter
        finally:
            self._drain_waiters.remove(waiter)
    def _get_close_waiter(self, stream):
        raise NotImplementedError
class StreamReaderProtocol(FlowControlMixin, protocols.Protocol):
    __doc__ = """Helper class to adapt between Protocol and StreamReader.

    (This is a helper class instead of making StreamReader itself a
    Protocol subclass, because the StreamReader has other potential
    uses, and to prevent the user of the StreamReader to accidentally
    call inappropriate methods of the protocol.)
    """
    _source_traceback = None
    def __init__(self, stream_reader, client_connected_cb=None, loop=None):
        super().__init__(loop=loop)
        if stream_reader is not None:
            self._stream_reader_wr = weakref.ref(stream_reader)
            self._source_traceback = stream_reader._source_traceback
        else:
            self._stream_reader_wr = None
        if client_connected_cb is not None:
            self._strong_reader = stream_reader
        self._reject_connection = False
        self._stream_writer = None
        self._task = None
        self._transport = None
        self._client_connected_cb = client_connected_cb
        self._over_ssl = False
        self._closed = self._loop.create_future()
    @property
    def _stream_reader(self):
        if self._stream_reader_wr is None:
            return None
        else:
            return self._stream_reader_wr()
    def _replace_writer(self, writer):
        loop = self._loop
        transport = writer.transport
        self._stream_writer = writer
        self._transport = transport
        self._over_ssl = transport.get_extra_info('sslcontext') is not None
    def connection_made(self, transport):
        if self._reject_connection:
            context = {'message': 'An open stream was garbage collected prior to establishing network connection; call "stream.close()" explicitly.'}
            if self._source_traceback:
                context['source_traceback'] = self._source_traceback
            self._loop.call_exception_handler(context)
            transport.abort()
            return None
        else:
            self._transport = transport
            reader = self._stream_reader
            if reader is not None:
                reader.set_transport(transport)
            self._over_ssl = transport.get_extra_info('sslcontext') is not None
            if self._client_connected_cb is not None:
                self._stream_writer = StreamWriter(transport, self, reader, self._loop)
                res = self._client_connected_cb(reader, self._stream_writer)
                if coroutines.iscoroutine(res):
                    def callback(task):
                        exc = task.exception()
                        if exc is not None:
                            self._loop.call_exception_handler({'message': 'Unhandled exception in client_connected_cb', 'exception': exc, 'transport': transport})
                            transport.close()
                            return None
                        else:
                            return None
                    self._task = self._loop.create_task(res)
                    self._task.add_done_callback(callback)
                self._strong_reader = None
                return None
            else:
                return None
    def connection_lost(self, exc):
        reader = self._stream_reader
        if reader is not None:
            if exc is None:
                reader.feed_eof()
            else:
                reader.set_exception(exc)
        if not self._closed.done():
            if exc is None:
                self._closed.set_result(None)
            else:
                self._closed.set_exception(exc)
        super().connection_lost(exc)
        self._stream_reader_wr = None
        self._stream_writer = None
        self._task = None
        self._transport = None
    def data_received(self, data):
        reader = self._stream_reader
        if reader is not None:
            reader.feed_data(data)
            return None
        else:
            return None
    def eof_received(self):
        reader = self._stream_reader
        if reader is not None:
            reader.feed_eof()
        if self._over_ssl:
            return False
        else:
            return True
    def _get_close_waiter(self, stream):
        return self._closed
    def __del__(self):
        try:
            closed = self._closed
        except AttributeError:
            return None
        else:
            if closed.done():
                if not closed.cancelled():
                    closed.exception()
                    return None
class StreamWriter:
    __doc__ = """Wraps a Transport.

    This exposes write(), writelines(), [can_]write_eof(),
    get_extra_info() and close().  It adds drain() which returns an
    optional Future on which you can wait for flow control.  It also
    adds a transport property which references the Transport
    directly.
    """
    def __init__(self, transport, protocol, reader, loop):
        self._transport = transport
        self._protocol = protocol
        if reader is not None:
            assert isinstance(reader, StreamReader)
        self._reader = reader
        self._loop = loop
        self._complete_fut = self._loop.create_future()
        self._complete_fut.set_result(None)
    def __repr__(self):
        info = [self.__class__.__name__, f'transport={self._transport!r}']
        if self._reader is not None:
            info.append(f'reader={self._reader!r}')
        return '<{}>'.format(' '.join(info))
    @property
    def transport(self):
        return self._transport
    def write(self, data):
        self._transport.write(data)
    def writelines(self, data):
        self._transport.writelines(data)
    def write_eof(self):
        return self._transport.write_eof()
    def can_write_eof(self):
        return self._transport.can_write_eof()
    def close(self):
        return self._transport.close()
    def is_closing(self):
        return self._transport.is_closing()
    async def wait_closed(self):
        await self._protocol._get_close_waiter(self)
    def get_extra_info(self, name, default=None):
        return self._transport.get_extra_info(name, default)
    async def drain(self):
        """Flush the write buffer.

        The intended use is to write

          w.write(data)
          await w.drain()
        """
        if self._reader is not None:
            exc = self._reader.exception()
            if exc is not None:
                raise exc
        return self._protocol._drain_helper()
    async def start_tls(self, sslcontext, *, server_hostname=None, ssl_handshake_timeout=None):
        """Upgrade an existing stream-based connection to TLS."""
        server_side = self._protocol._client_connected_cb is not None
        protocol = self._protocol
        await self.drain()
        new_transport = await self._loop.start_tls(self._transport, protocol, sslcontext, server_side=server_side, server_hostname=server_hostname, ssl_handshake_timeout=ssl_handshake_timeout)
        self._transport = new_transport
        protocol._replace_writer(self)
    def __del__(self):
        if not self._transport.is_closing():
            if self._loop.is_closed():
                warnings.warn('loop is closed', ResourceWarning)
                return None
            else:
                self.close()
                warnings.warn(f'unclosed {self!r}', ResourceWarning)
        else:
            return None
class StreamReader:
    _source_traceback = None
    def __init__(self, limit=_DEFAULT_LIMIT, loop=None):
        if limit <= 0:
            raise ValueError('Limit cannot be <= 0')
        self._limit = limit
        if loop is None:
            self._loop = events._get_event_loop()
        else:
            self._loop = loop
        self._buffer = bytearray()
        self._eof = False
        self._waiter = None
        self._exception = None
        self._transport = None
        self._paused = False
        if self._loop.get_debug():
            self._source_traceback = format_helpers.extract_stack(sys._getframe(1))
            return None
        else:
            return None
    def __repr__(self):
        info = ['StreamReader']
        if self._buffer:
            info.append(f'{len(self._buffer)} bytes')
        if self._eof:
            info.append('eof')
        if self._limit != _DEFAULT_LIMIT:
            info.append(f'limit={self._limit}')
        if self._waiter:
            info.append(f'waiter={self._waiter!r}')
        if self._exception:
            info.append(f'exception={self._exception!r}')
        if self._transport:
            info.append(f'transport={self._transport!r}')
        if self._paused:
            info.append('paused')
        return '<{}>'.format(' '.join(info))
    def exception(self):
        return self._exception
    def set_exception(self, exc):
        self._exception = exc
        waiter = self._waiter
        if waiter is not None:
            self._waiter = None
            if not waiter.cancelled():
                waiter.set_exception(exc)
                return None
    def _wakeup_waiter(self):
        """Wakeup read*() functions waiting for data or EOF."""
        waiter = self._waiter
        if waiter is not None:
            self._waiter = None
            if not waiter.cancelled():
                waiter.set_result(None)
                return None
    def set_transport(self, transport):
        assert self._transport is None, 'Transport already set'
        self._transport = transport
    def _maybe_resume_transport(self):
        if self._paused:
            if len(self._buffer) <= self._limit:
                self._paused = False
                self._transport.resume_reading()
                return None
    def feed_eof(self):
        self._eof = True
        self._wakeup_waiter()
    def at_eof(self):
        """Return True if the buffer is empty and 'feed_eof' was called."""
        return self._eof and not self._buffer
    def feed_data(self, data):
        assert self._eof, 'feed_data after feed_eof'
        if not data:
            return None
        else:
            self._buffer.extend(data)
            self._wakeup_waiter()
            if self._transport is not None:
                if not self._paused:
                    if len(self._buffer) > 2 * self._limit:
                        try:
                            self._transport.pause_reading()
                        except NotImplementedError:
                            self._transport = None
                            return None
                        else:
                            self._paused = True
                            return None
    async def _wait_for_data(self, func_name):
        """Wait until feed_data() or feed_eof() is called.

        If stream was paused, automatically resume it.
        """
        if self._waiter is not None:
            raise RuntimeError(f'{func_name}() called while another coroutine is already waiting for incoming data')
        assert self._eof, '_wait_for_data after EOF'
        if self._paused:
            self._paused = False
            self._transport.resume_reading()
        self._waiter = self._loop.create_future()
        try:
            await self._waiter
        finally:
            self._waiter = None
    async def readline(self):
        """Read chunk of data from the stream until newline (b'
') is found.

        On success, return chunk that ends with newline. If only partial
        line can be read due to EOF, return incomplete line without
        terminating newline. When EOF was reached while no bytes read, empty
        bytes object is returned.

        If limit is reached, ValueError will be raised. In that case, if
        newline was found, complete line including newline will be removed
        from internal buffer. Else, internal buffer will be cleared. Limit is
        compared against part of the line without newline.

        If stream was paused, this function will automatically resume it if
        needed.
        """
        sep = b'\n'
        seplen = len(sep)
        try:
            line = await self.readuntil(sep)
        except exceptions.IncompleteReadError as e:
            return e.partial
        except exceptions.LimitOverrunError as e:
            if self._buffer.startswith(sep, e.consumed):
                del (self._buffer[:e.consumed + seplen])
            else:
                self._buffer.clear()
            self._maybe_resume_transport()
            raise ValueError(e.args[0])
        return line
    async def readuntil(self, separator=b'\n'):
        """Read data from the stream until ``separator`` is found.

        On success, the data and separator will be removed from the
        internal buffer (consumed). Returned data will include the
        separator at the end.

        Configured stream limit is used to check result. Limit sets the
        maximal length of data that can be returned, not counting the
        separator.

        If an EOF occurs and the complete separator is still not found,
        an IncompleteReadError exception will be raised, and the internal
        buffer will be reset.  The IncompleteReadError.partial attribute
        may contain the separator partially.

        If the data cannot be read because of over limit, a
        LimitOverrunError exception  will be raised, and the data
        will be left in the internal buffer, so it can be read again.
        """
        seplen = len(separator)
        if seplen == 0:
            raise ValueError('Separator should be at least one-byte string')
        elif self._exception is not None:
            raise self._exception
        else:
            offset = 0
        while True:
            buflen = len(self._buffer)
            if buflen - offset >= seplen:
                isep = self._buffer.find(separator, offset)
                if isep != -1:
                    break
                offset = buflen + 1 - seplen
                if offset > self._limit:
                    raise exceptions.LimitOverrunError('Separator is not found, and chunk exceed the limit', offset)
                break
            if self._eof:
                chunk = bytes(self._buffer)
                self._buffer.clear()
                raise exceptions.IncompleteReadError(chunk, None)
            await self._wait_for_data('readuntil')
        if isep > self._limit:
            raise exceptions.LimitOverrunError('Separator is found, but chunk is longer than limit', isep)
        chunk = self._buffer[:isep + seplen]
        del (self._buffer[:isep + seplen])
        self._maybe_resume_transport()
        return bytes(chunk)
    async def read(self, n=-1):
        """Read up to `n` bytes from the stream.

        If `n` is not provided or set to -1,
        read until EOF, then return all read bytes.
        If EOF was received and the internal buffer is empty,
        return an empty bytes object.

        If `n` is 0, return an empty bytes object immediately.

        If `n` is positive, return at most `n` available bytes
        as soon as at least 1 byte is available in the internal buffer.
        If EOF is received before any byte is read, return an empty
        bytes object.

        Returned value is not limited with limit, configured at stream
        creation.

        If stream was paused, this function will automatically resume it if
        needed.
        """
        if self._exception is not None:
            raise self._exception
        elif n == 0:
            return b''
        elif n < 0:
            blocks = []
            while True:
                if not await self.read(self._limit):
                    break
                blocks.append(block)
            if n < 0:
                return b''.join(blocks)
            elif not (self._buffer or self._eof):
                await self._wait_for_data('read')
        elif not (self._buffer or self._eof):
            pass
    async def readexactly(self, n):
        """Read exactly `n` bytes.

        Raise an IncompleteReadError if EOF is reached before `n` bytes can be
        read. The IncompleteReadError.partial attribute of the exception will
        contain the partial read bytes.

        if n is zero, return empty bytes object.

        Returned value is not limited with limit, configured at stream
        creation.

        If stream was paused, this function will automatically resume it if
        needed.
        """
        if n < 0:
            raise ValueError('readexactly size can not be less than zero')
        elif self._exception is not None:
            raise self._exception
        elif n == 0:
            return b''
        else:
            while len(self._buffer) < n:
                if self._eof:
                    incomplete = bytes(self._buffer)
                    self._buffer.clear()
                    raise exceptions.IncompleteReadError(incomplete, n)
                await self._wait_for_data('readexactly')
            if len(self._buffer) == n:
                data = bytes(self._buffer)
                self._buffer.clear()
            else:
                data = bytes(self._buffer[:n])
                del (self._buffer[:n])
            self._maybe_resume_transport()
            return data
    def __aiter__(self):
        return self
    async def __anext__(self):
        if await self.readline() == b'':
            raise StopAsyncIteration
        return val
