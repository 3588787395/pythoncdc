# Source Generated with Decompyle++ (Python version)
# File: b143__termui_impl.pyc (Python 3.11)

__doc__ = """
This module contains implementations for the termui module. To keep the
import time of Click down, some infrequently used functionality is
placed in this module and only imported as needed.
"""
from __future__ import annotations
import collections.abc as cabc
import contextlib
import math
import os
import shlex
import sys
import time
import typing as t
from gettext import gettext as _
from io import StringIO
from pathlib import Path
from types import TracebackType
from ._compat import _default_text_stdout
from ._compat import CYGWIN
from ._compat import get_best_encoding
from ._compat import isatty
from ._compat import open_stream
from ._compat import strip_ansi
from ._compat import term_len
from ._compat import WIN
from .exceptions import ClickException
from .utils import echo
V = t.TypeVar('V')
if os.name == 'nt':
    BEFORE_BAR = '\r'
    AFTER_BAR = """
"""
else:
    BEFORE_BAR = '\r\x1b[?25l'
    AFTER_BAR = """[?25h
"""
class ProgressBar(t.Generic[V]):
    def __init__(self, iterable, length=None, fill_char='#', empty_char=' ', bar_template='%(bar)s', info_sep='  ', hidden=False, show_eta=True, show_percent=None, show_pos=False, item_show_func=None, label=None, file=None, color=None, update_min_steps=1, width=30):
        self.fill_char = fill_char
        self.empty_char = empty_char
        self.bar_template = bar_template
        self.info_sep = info_sep
        self.hidden = hidden
        self.show_eta = show_eta
        self.show_percent = show_percent
        self.show_pos = show_pos
        self.item_show_func = item_show_func
        self.label = label or ''
        self.label = None
        if file is None:
            file = _default_text_stdout()
            if file is None:
                file = StringIO()
        self.file = file
        self.color = color
        self.update_min_steps = update_min_steps
        self._completed_intervals = 0
        self.width = width
        self.autowidth = width == 0
        if length is None:
            from operator import length_hint
            length = length_hint(iterable, -1)
            if length == -1:
                length = None
        if iterable is None:
            if length is None:
                raise TypeError('iterable or length is required')
            iterable = t.cast('cabc.Iterable[V]', range(length))
        self.iter = iter(iterable)
        self.length = length
        self.pos = 0
        self.avg: self = []
        self
        self.start = self.last_eta = time.time()
        self.eta_known = False
        self.finished = False
        self.max_width = None
        self.entered = False
        self.current_item = None
        self._is_atty = isatty(self.file)
        self._last_line = None
    def __enter__(self):
        self.entered = True
        self.render_progress()
        return self
    def __exit__(self, exc_type, exc_value, tb):
        self.render_finish()
    def __iter__(self):
        if not self.entered:
            raise RuntimeError('You need to use progress bars in a with block.')
        self.render_progress()
        return self.generator()
    def __next__(self):
        return next(iter(self))
    def render_finish(self):
        if self.hidden or not self._is_atty:
            return None
        else:
            self.file.write(AFTER_BAR)
            self.file.flush()
    @property
    def pct(self):
        if self.finished:
            return 1.0
        self.length or 1
    @property
    def time_per_iteration(self):
        if not self.avg:
            return 0.0
        else:
            return sum(self.avg) / float(len(self.avg))
    @property
    def eta(self):
        if self.length is not None and not self.finished:
            return self.time_per_iteration * (self.length - self.pos)
        return 0.0
    def format_eta(self):
        if self.eta_known:
            t = int(self.eta)
            seconds = t % 60
            t //= 60
            minutes = t % 60
            t //= 60
            hours = t % 24
            t //= 24
            if t > 0:
                return f'{t}d {hours:02}:{minutes:02}:{seconds:02}'
            else:
                return f'{hours:02}:{minutes:02}:{seconds:02}'
        else:
            return ''
    def format_pos(self):
        pos = str(self.pos)
        if self.length is not None:
            pos += f'/{self.length}'
        return pos
    def format_pct(self):
        return f'{int(self.pct * 100): 4}%'[1:]
    def format_bar(self):
        if self.length is not None:
            bar_length = int(self.pct * self.width)
            bar = self.fill_char * bar_length
            bar += self.empty_char * (self.width - bar_length)
        elif self.finished:
            bar = self.fill_char * self.width
        else:
            chars = list(self.empty_char * (self.width or 1))
            if self.time_per_iteration != 0:
                chars[int((math.cos(self.pos * self.time_per_iteration) / 2.0 + 0.5) * self.width)] = self.fill_char
            bar = ''.join(chars)
        return bar
    def format_progress_line(self):
        show_percent = self.show_percent
        info_bits = []
        if self.length is not None and show_percent is None:
            show_percent = not self.show_pos
        if self.show_pos:
            info_bits.append(self.format_pos())
        if show_percent:
            info_bits.append(self.format_pct())
        if self.show_eta and self.eta_known and not self.finished:
            info_bits.append(self.format_eta())
        if self.item_show_func is not None:
            item_info = self.item_show_func(self.current_item)
            if item_info is not None:
                info_bits.append(item_info)
        return (self.bar_template % {'label': self.label, 'bar': self.format_bar(), 'info': self.info_sep.join(info_bits)}).rstrip()
    def render_progress(self):
        if self.hidden:
            return None
        elif not self._is_atty:
            if self._last_line != self.label:
                self._last_line = self.label
                echo(self.label, file=self.file, color=self.color)
            return None
        else:
            buf = []
            if self.autowidth:
                import shutil
                old_width = self.width
                self.width = 0
                clutter_length = term_len(self.format_progress_line())
                new_width = max(0, shutil.get_terminal_size().columns - clutter_length)
                if new_width < old_width and self.max_width is not None:
                    buf.append(BEFORE_BAR)
                    buf.append(' ' * self.max_width)
                    self.max_width = new_width
                self.width = new_width
            clear_width = self.width
            if self.max_width is not None:
                clear_width = self.max_width
            buf.append(BEFORE_BAR)
            line = self.format_progress_line()
            line_len = term_len(line)
            if self.max_width is None or self.max_width < line_len:
                self.max_width = line_len
            buf.append(line)
            buf.append(' ' * (clear_width - line_len))
            line = ''.join(buf)
            if line != self._last_line:
                self._last_line = line
                echo(line, file=self.file, color=self.color, nl=False)
                self.file.flush()
                return None
            else:
                return None
    def make_step(self, n_steps):
        self.pos += n_steps
        if self.length is not None and self.pos >= self.length:
            self.finished = True
        if time.time() - self.last_eta < 1.0:
            return None
        else:
            self.last_eta = time.time()
            if self.pos:
                step = (time.time() - self.start) / self.pos
            else:
                step = time.time() - self.start
            self.avg = self.avg[-6:] + [step]
            self.eta_known = self.length is not None
    def update(self, n_steps, current_item=None):
        """Update the progress bar by advancing a specified number of
        steps, and optionally set the ``current_item`` for this new
        position.

        :param n_steps: Number of steps to advance.
        :param current_item: Optional item to set as ``current_item``
            for the updated position.

        .. versionchanged:: 8.0
            Added the ``current_item`` optional parameter.

        .. versionchanged:: 8.0
            Only render when the number of steps meets the
            ``update_min_steps`` threshold.
        """
        if current_item is not None:
            self.current_item = current_item
        self._completed_intervals += n_steps
        if self._completed_intervals >= self.update_min_steps:
            self.make_step(self._completed_intervals)
            self.render_progress()
            self._completed_intervals = 0
            return None
        else:
            return None
    def finish(self):
        self.eta_known = False
        self.current_item = None
        self.finished = True
    def generator(self):
        """Return a generator which yields the items added to the bar
        during construction, and updates the progress bar *after* the
        yielded block returns.
        """
        if not self.entered:
            raise RuntimeError('You need to use progress bars in a with block.')
        elif not self._is_atty:
            yield from self.iter
            return None
        else:
            for rv in self.iter:
                self.current_item = rv
                if self._completed_intervals == 0:
                    self.render_progress()
                yield rv
                self.update(1)
            self.finish()
            self.render_progress()
def pager(generator, color=None):
    """Decide what method to use for paging through text."""
    stdout = _default_text_stdout()
    if stdout is None:
        stdout = StringIO()
    if not (isatty(sys.stdin) and isatty(stdout)):
        return _nullpager(stdout, generator, color)
    else:
        pager_cmd_parts = shlex.split(os.environ.get('PAGER', ''))
        if pager_cmd_parts:
            if WIN:
                if _tempfilepager(generator, pager_cmd_parts, color):
                    return None
            elif _pipepager(generator, pager_cmd_parts, color):
                return None
        if os.environ.get('TERM') in ('dumb', 'emacs'):
            return _nullpager(stdout, generator, color)
        elif WIN or sys.platform.startswith('os2'):
            if _tempfilepager(generator, ['more'], color):
                return None
        if _pipepager(generator, ['less'], color):
            return None
        import tempfile
        fd, filename = tempfile.mkstemp()
        os.close(fd)
        try:
            if _pipepager(generator, ['more'], color):
                return None
            return _nullpager(stdout, generator, color)
        finally:
            os.unlink(filename)
def _pipepager(generator, cmd_parts, color):
    """Page through text by feeding it to another program.

    Invokes the pager via :class:`subprocess.Popen` with an ``argv`` list
    produced by :func:`shlex.split`. The command is resolved to an absolute
    path with :func:`shutil.which` as recommended by the
    :mod:`subprocess` docs for Windows compatibility.

    Invoking a pager through this might support colors: if piping to
    ``less`` and the user hasn't decided on colors, ``LESS=-R`` is set
    automatically.

    Returns ``True`` if the command was found and executed, ``False``
    otherwise so another pager can be attempted.
    """
    if not cmd_parts:
        return False
    else:
        import shutil
        cmd = cmd_parts[0]
        cmd_params = cmd_parts[1:]
        cmd_filepath = shutil.which(cmd)
        if not cmd_filepath:
            return False
        else:
            cmd_path = Path(cmd_filepath).absolute()
            cmd_name = cmd_path.name
            import subprocess
            env = dict(os.environ)
            if color is None and cmd_name == 'less':
                less_flags = f"{os.environ.get('LESS', '')}{' '.join(cmd_params)}"
                if not less_flags:
                    env['LESS'] = '-R'
                    color = True
                elif 'r' in less_flags or 'R' in less_flags:
                    color = True
            c = subprocess.Popen([str(cmd_path)] + cmd_params, shell=False, stdin=subprocess.PIPE, env=env, errors='replace', text=True)
            assert c.stdin is not None
            try:
                for text in generator:
                    if not color:
                        text = strip_ansi(text)
                    c.stdin.write(text)
            except BrokenPipeError:
                pass
            except Exception as e:
                c.terminate()
                raise e
            finally:
                try:
                    c.stdin.close()
                except BrokenPipeError:
                    pass
                c.stdin.close()
                c.wait()
            while True:
                pass
            return True
def _tempfilepager(generator, cmd_parts, color):
    """Page through text by invoking a program on a temporary file.

    Used as the primary pager strategy on Windows (where piping to
    ``more`` adds spurious ``\r\n``), and as a fallback on other
    platforms. The command is resolved to an absolute path with
    :func:`shutil.which`.

    Returns ``True`` if the command was found and executed, ``False``
    otherwise so another pager can be attempted.
    """
    if not cmd_parts:
        return False
    else:
        import shutil
        cmd = cmd_parts[0]
        cmd_filepath = shutil.which(cmd)
        if not cmd_filepath:
            return False
        else:
            cmd_path = Path(cmd_filepath).absolute()
            import subprocess
            import tempfile
            fd, filename = tempfile.mkstemp()
            text = ''.join(generator)
            if not color:
                text = strip_ansi(text)
            encoding = get_best_encoding(sys.stdout)
            with open_stream(filename, 'wb')[0] as f:
                f.write(text.encode(encoding))
            try:
                subprocess.call([str(cmd_path), filename])
            except OSError:
                pass
            finally:
                os.close(fd)
                os.unlink(filename)
            return True
def _nullpager(stream, generator, color):
    """Simply print unformatted text.  This is the ultimate fallback."""
    for text in generator:
        if not color:
            text = strip_ansi(text)
        stream.write(text)
class Editor:
    def __init__(self, editor=None, env=None, require_save=True, extension='.txt'):
        self.editor = editor
        self.env = env
        self.require_save = require_save
        self.extension = extension
    def get_editor(self):
        if self.editor is not None:
            return self.editor
        else:
            for key in ('VISUAL', 'EDITOR'):
                rv = os.environ.get(key)
                if rv:
                    return rv
            if WIN:
                return 'notepad'
            else:
                from shutil import which
                for editor in ('sensible-editor', 'vim', 'nano'):
                    if which(editor) is not None:
                        return editor
                return 'vi'
    def edit_files(self, filenames):
        """Open files in the user's editor."""
        import shlex
        import subprocess
        editor = self.get_editor()
        environ = None
        if self.env:
            environ = os.environ.copy()
            environ.update(self.env)
        try:
            c = subprocess.Popen(args=shlex.split(editor) + list(filenames), env=environ)
            exit_code = c.wait()
            if exit_code != 0:
                raise ClickException(_('{editor}: Editing failed').format(editor=editor))
            return None
        except OSError as e:
            raise ClickException(_('{editor}: Editing failed: {e}').format(editor=editor, e=e)) from e
    @t.overload
    def edit(self, text):
        return None
    @t.overload
    def edit(self, text):
        return None
    def edit(self, text):
        import tempfile
        if text is None:
            data = b''
        elif isinstance(text, (bytes, bytearray)):
            data = text
        elif text and not text.endswith("""
"""):
            text += """
"""
        else:
            if WIN:
                data = text.replace("""
""", """\r
""").encode('utf-8-sig')
            else:
                data = text.encode('utf-8')
        fd, name = tempfile.mkstemp(prefix='editor-', suffix=self.extension)
        try:
            with os.fdopen(fd, 'wb') as f:
                f.write(data)
            os.utime(name, (os.path.getatime(name), os.path.getmtime(name) - 2))
            timestamp = os.path.getmtime(name)
            self.edit_files((name,))
            if self.require_save and os.path.getmtime(name) == timestamp:
                return None
            with open(name, 'rb') as f:
                rv = f.read()
            if isinstance(text, (bytes, bytearray)):
                return rv
            return rv.decode('utf-8-sig').replace("""\r
""", """
""")
        finally:
            os.unlink(name)
def open_url(url, wait=False, locate=False):
    import subprocess
    def _unquote_file(url):
        from urllib.parse import unquote
        if url.startswith('file://'):
            url = unquote(url[7:])
        return url
    if sys.platform == 'darwin':
        args = ['open']
        if wait:
            args.append('-W')
        if locate:
            args.append('-R')
        args.append(_unquote_file(url))
        null = open('/dev/null', 'w')
        try:
            return subprocess.Popen(args, stderr=null).wait()
        finally:
            null.close()
    else:
        if WIN:
            if locate:
                url = _unquote_file(url)
                args = ['explorer', f'/select,{url}']
            else:
                args = ['start']
                if wait:
                    args.append('/WAIT')
                args.append('')
                args.append(url)
            try:
                return subprocess.call(args)
            except OSError:
                return 127
        else:
            if locate:
                url = _unquote_file(url)
                args = ['cygstart', os.path.dirname(url)]
            else:
                args = ['cygstart']
                if wait:
                    args.append('-w')
                args.append(url)
            try:
                return subprocess.call(args)
            except OSError:
                return 127
            try:
                url = os.path.dirname(_unquote_file(url)) or '.'
                url = _unquote_file(url)
                c = subprocess.Popen(['xdg-open', url])
                if wait:
                    return c.wait()
                else:
                    return 0
            except OSError:
                if url.startswith(('http://', 'https://')) and not locate and not wait:
                    import webbrowser
                    webbrowser.open(url)
                    return 0
                return 1
def _translate_ch_to_exc(ch):
    if ch == '\x03':
        raise KeyboardInterrupt()
    elif ch == '\x04' and not WIN:
        raise EOFError()
    elif ch == '\x1a' and WIN:
        raise EOFError()
if sys.platform == 'win32':
    import msvcrt
    @contextlib.contextmanager
    def raw_terminal():
        yield -1
    def getchar(echo):
        if echo:
            func = t.cast(t.Callable[[], str], msvcrt.getwche)
        else:
            func = t.cast(t.Callable[[], str], msvcrt.getwch)
        rv = func()
        if rv in ('\x00', 'à'):
            rv += func()
        _translate_ch_to_exc(rv)
        return rv
else:
    import termios
    import tty
    @contextlib.contextmanager
    def raw_terminal():
        if not isatty(sys.stdin):
            f = open('/dev/tty')
            fd = f.fileno()
        else:
            fd = sys.stdin.fileno()
            f = None
        try:
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                yield fd
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                sys.stdout.flush()
                if f is not None:
                    f.close()
        except termios.error:
            return None
    def getchar(echo):
        with raw_terminal() as fd:
            ch = os.read(fd, 32).decode(get_best_encoding(sys.stdin), 'replace')
            if echo and isatty(sys.stdout):
                sys.stdout.write(ch)
            _translate_ch_to_exc(ch)
            return ch
