# Source Generated with Decompyle++ (Python version)
# File: b142__freeimage.pyc (Python 3.11)

__doc__ = """Module imageio/freeimage.py

This module contains the wrapper code for the freeimage library.
The functions defined in this module are relatively thin; just thin
enough so that arguments and results are native Python/numpy data
types.

"""
import os
import sys
import ctypes
import threading
import logging
import numpy
from ..core import get_remote_file, load_lib, Dict, resource_dirs, IS_PYPY, get_platform, InternetNotAllowedError, NeedDownloadError
logger = logging.getLogger(__name__)
TEST_NUMPY_NO_STRIDES = False
FNAME_PER_PLATFORM = {'osx32': 'libfreeimage-3.16.0-osx10.6.dylib', 'osx64': 'libfreeimage-3.16.0-osx10.6.dylib', 'win32': 'FreeImage-3.18.0-win32.dll', 'win64': 'FreeImage-3.18.0-win64.dll', 'linux32': 'libfreeimage-3.16.0-linux32.so', 'linux64': 'libfreeimage-3.16.0-linux64.so'}
def download(directory=None, force_download=False):
    """Download the FreeImage library to your computer.

    Parameters
    ----------
    directory : str | None
        The directory where the file will be cached if a download was
        required to obtain the file. By default, the appdata directory
        is used. This is also the first directory that is checked for
        a local version of the file.
    force_download : bool | str
        If True, the file will be downloaded even if a local copy exists
        (and this copy will be overwritten). Can also be a YYYY-MM-DD date
        to ensure a file is up-to-date (modified date of a file on disk,
        if present, is checked).
    """
    plat = get_platform()
    if plat:
        if plat in FNAME_PER_PLATFORM:
            fname = 'freeimage/' + FNAME_PER_PLATFORM[plat]
            get_remote_file(fname=fname, directory=directory, force_download=force_download)
            fi._lib = None
            return None
def get_freeimage_lib():
    """Ensure we have our version of the binary freeimage lib."""
    lib = os.getenv('IMAGEIO_FREEIMAGE_LIB', None)
    if lib:
        return lib
    else:
        plat = get_platform()
        if plat:
            if plat in FNAME_PER_PLATFORM:
                try:
                    return get_remote_file('freeimage/' + FNAME_PER_PLATFORM[plat], auto=False)
                except InternetNotAllowedError:
                    return None
                except NeedDownloadError:
                    raise NeedDownloadError("""Need FreeImage library. You can obtain it with either:
  - download using the command: imageio_download_bin freeimage
  - download by calling (in Python): imageio.plugins.freeimage.download()
""")
                except RuntimeError as e:
                    logger.warning(str(e))
                    return None
def efn(x):
    return x.encode(sys.getfilesystemencoding())
GREY_PALETTE = numpy.arange(0, 16777216, 65793, dtype=numpy.uint32)
class FI_TYPES(object):
    FIT_UNKNOWN = 0
    FIT_BITMAP = 1
    FIT_UINT16 = 2
    FIT_INT16 = 3
    FIT_UINT32 = 4
    FIT_INT32 = 5
    FIT_FLOAT = 6
    FIT_DOUBLE = 7
    FIT_COMPLEX = 8
    FIT_RGB16 = 9
    FIT_RGBA16 = 10
    FIT_RGBF = 11
    FIT_RGBAF = 12
    dtypes = {FIT_BITMAP: numpy.uint8, FIT_UINT16: numpy.uint16, FIT_INT16: numpy.int16, FIT_UINT32: numpy.uint32, FIT_INT32: numpy.int32, FIT_FLOAT: numpy.float32, FIT_DOUBLE: numpy.float64, FIT_COMPLEX: numpy.complex128, FIT_RGB16: numpy.uint16, FIT_RGBA16: numpy.uint16, FIT_RGBF: numpy.float32, FIT_RGBAF: numpy.float32}
    fi_types = {(numpy.uint8, 1): FIT_BITMAP, (numpy.uint8, 3): FIT_BITMAP, (numpy.uint8, 4): FIT_BITMAP, (numpy.uint16, 1): FIT_UINT16, (numpy.int16, 1): FIT_INT16, (numpy.uint32, 1): FIT_UINT32, (numpy.int32, 1): FIT_INT32, (numpy.float32, 1): FIT_FLOAT, (numpy.float64, 1): FIT_DOUBLE, (numpy.complex128, 1): FIT_COMPLEX, (numpy.uint16, 3): FIT_RGB16, (numpy.uint16, 4): FIT_RGBA16, (numpy.float32, 3): FIT_RGBF, (numpy.float32, 4): FIT_RGBAF}
    extra_dims = {FIT_UINT16: [], FIT_INT16: [], FIT_UINT32: [], FIT_INT32: [], FIT_FLOAT: [], FIT_DOUBLE: [], FIT_COMPLEX: [], FIT_RGB16: [3], FIT_RGBA16: [4], FIT_RGBF: [3], FIT_RGBAF: [4]}
class IO_FLAGS(object):
    FIF_LOAD_NOPIXELS = 32768
    BMP_DEFAULT = 0
    BMP_SAVE_RLE = 1
    CUT_DEFAULT = 0
    DDS_DEFAULT = 0
    EXR_DEFAULT = 0
    EXR_FLOAT = 1
    EXR_NONE = 2
    EXR_ZIP = 4
    EXR_PIZ = 8
    EXR_PXR24 = 16
    EXR_B44 = 32
    EXR_LC = 64
    FAXG3_DEFAULT = 0
    GIF_DEFAULT = 0
    GIF_LOAD256 = 1
    GIF_PLAYBACK = 2
    HDR_DEFAULT = 0
    ICO_DEFAULT = 0
    ICO_MAKEALPHA = 1
    IFF_DEFAULT = 0
    J2K_DEFAULT = 0
    JP2_DEFAULT = 0
    JPEG_DEFAULT = 0
    JPEG_FAST = 1
    JPEG_ACCURATE = 2
    JPEG_CMYK = 4
    JPEG_EXIFROTATE = 8
    JPEG_QUALITYSUPERB = 128
    JPEG_QUALITYGOOD = 256
    JPEG_QUALITYNORMAL = 512
    JPEG_QUALITYAVERAGE = 1024
    JPEG_QUALITYBAD = 2048
    JPEG_PROGRESSIVE = 8192
    JPEG_SUBSAMPLING_411 = 4096
    JPEG_SUBSAMPLING_420 = 16384
    JPEG_SUBSAMPLING_422 = 32768
    JPEG_SUBSAMPLING_444 = 65536
    JPEG_OPTIMIZE = 131072
    JPEG_BASELINE = 262144
    KOALA_DEFAULT = 0
    LBM_DEFAULT = 0
    MNG_DEFAULT = 0
    PCD_DEFAULT = 0
    PCD_BASE = 1
    PCD_BASEDIV4 = 2
    PCD_BASEDIV16 = 3
    PCX_DEFAULT = 0
    PFM_DEFAULT = 0
    PICT_DEFAULT = 0
    PNG_DEFAULT = 0
    PNG_IGNOREGAMMA = 1
    PNG_Z_BEST_SPEED = 1
    PNG_Z_DEFAULT_COMPRESSION = 6
    PNG_Z_BEST_COMPRESSION = 9
    PNG_Z_NO_COMPRESSION = 256
    PNG_INTERLACED = 512
    PNM_DEFAULT = 0
    PNM_SAVE_RAW = 0
    PNM_SAVE_ASCII = 1
    PSD_DEFAULT = 0
    PSD_CMYK = 1
    PSD_LAB = 2
    RAS_DEFAULT = 0
    RAW_DEFAULT = 0
    RAW_PREVIEW = 1
    RAW_DISPLAY = 2
    SGI_DEFAULT = 0
    TARGA_DEFAULT = 0
    TARGA_LOAD_RGB888 = 1
    TARGA_SAVE_RLE = 2
    TIFF_DEFAULT = 0
    TIFF_CMYK = 1
    TIFF_PACKBITS = 256
    TIFF_DEFLATE = 512
    TIFF_ADOBE_DEFLATE = 1024
    TIFF_NONE = 2048
    TIFF_CCITTFAX3 = 4096
    TIFF_CCITTFAX4 = 8192
    TIFF_LZW = 16384
    TIFF_JPEG = 32768
    TIFF_LOGLUV = 65536
    WBMP_DEFAULT = 0
    XBM_DEFAULT = 0
    XPM_DEFAULT = 0
class METADATA_MODELS(object):
    FIMD_COMMENTS = 0
    FIMD_EXIF_MAIN = 1
    FIMD_EXIF_EXIF = 2
    FIMD_EXIF_GPS = 3
    FIMD_EXIF_MAKERNOTE = 4
    FIMD_EXIF_INTEROP = 5
    FIMD_IPTC = 6
    FIMD_XMP = 7
    FIMD_GEOTIFF = 8
    FIMD_ANIMATION = 9
class METADATA_DATATYPE(object):
    FIDT_BYTE = 1
    FIDT_ASCII = 2
    FIDT_SHORT = 3
    FIDT_LONG = 4
    FIDT_RATIONAL = 5
    FIDT_SBYTE = 6
    FIDT_UNDEFINED = 7
    FIDT_SSHORT = 8
    FIDT_SLONG = 9
    FIDT_SRATIONAL = 10
    FIDT_FLOAT = 11
    FIDT_DOUBLE = 12
    FIDT_IFD = 13
    FIDT_PALETTE = 14
    FIDT_LONG8 = 16
    FIDT_SLONG8 = 17
    FIDT_IFD8 = 18
    dtypes = {FIDT_BYTE: numpy.uint8, FIDT_SHORT: numpy.uint16, FIDT_LONG: numpy.uint32, FIDT_RATIONAL: [('numerator', numpy.uint32), ('denominator', numpy.uint32)], FIDT_LONG8: numpy.uint64, FIDT_SLONG8: numpy.int64, FIDT_IFD8: numpy.uint64, FIDT_SBYTE: numpy.int8, FIDT_UNDEFINED: numpy.uint8, FIDT_SSHORT: numpy.int16, FIDT_SLONG: numpy.int32, FIDT_SRATIONAL: [('numerator', numpy.int32), ('denominator', numpy.int32)], FIDT_FLOAT: numpy.float32, FIDT_DOUBLE: numpy.float64, FIDT_IFD: numpy.uint32, FIDT_PALETTE: [('R', numpy.uint8), ('G', numpy.uint8), ('B', numpy.uint8), ('A', numpy.uint8)]}
class Freeimage(object):
    __doc__ = """Class to represent an interface to the FreeImage library.
    This class is relatively thin. It provides a Pythonic API that converts
    Freeimage objects to Python objects, but that's about it.
    The actual implementation should be provided by the plugins.

    The recommended way to call into the Freeimage library (so that
    errors and warnings show up in the right moment) is to use this
    object as a context manager:
    with imageio.fi as lib:
        lib.FreeImage_GetPalette()

    """
    _API = {'FreeImage_AllocateT': (ctypes.c_void_p, None), 'FreeImage_FindFirstMetadata': (ctypes.c_void_p, None), 'FreeImage_GetBits': (ctypes.c_void_p, None), 'FreeImage_GetPalette': (ctypes.c_void_p, None), 'FreeImage_GetTagKey': (ctypes.c_char_p, None), 'FreeImage_GetTagValue': (ctypes.c_void_p, None), 'FreeImage_CreateTag': (ctypes.c_void_p, None), 'FreeImage_Save': (ctypes.c_void_p, None), 'FreeImage_Load': (ctypes.c_void_p, None), 'FreeImage_LoadFromMemory': (ctypes.c_void_p, None), 'FreeImage_OpenMultiBitmap': (ctypes.c_void_p, None), 'FreeImage_LoadMultiBitmapFromMemory': (ctypes.c_void_p, None), 'FreeImage_LockPage': (ctypes.c_void_p, None), 'FreeImage_OpenMemory': (ctypes.c_void_p, None), 'FreeImage_GetVersion': (ctypes.c_char_p, None), 'FreeImage_GetFIFExtensionList': (ctypes.c_char_p, None), 'FreeImage_GetFormatFromFIF': (ctypes.c_char_p, None), 'FreeImage_GetFIFDescription': (ctypes.c_char_p, None), 'FreeImage_ColorQuantizeEx': (ctypes.c_void_p, None), 'FreeImage_IsLittleEndian': (ctypes.c_int, None), 'FreeImage_SetOutputMessage': (ctypes.c_void_p, None), 'FreeImage_GetFIFCount': (ctypes.c_int, None), 'FreeImage_IsPluginEnabled': (ctypes.c_int, None), 'FreeImage_GetFileType': (ctypes.c_int, None), 'FreeImage_GetTagType': (ctypes.c_int, None), 'FreeImage_GetTagLength': (ctypes.c_int, None), 'FreeImage_FindNextMetadata': (ctypes.c_int, None), 'FreeImage_FindCloseMetadata': (ctypes.c_void_p, None), 'FreeImage_GetFIFFromFilename': (ctypes.c_int, None), 'FreeImage_FIFSupportsReading': (ctypes.c_int, None), 'FreeImage_FIFSupportsWriting': (ctypes.c_int, None), 'FreeImage_FIFSupportsExportType': (ctypes.c_int, None), 'FreeImage_FIFSupportsExportBPP': (ctypes.c_int, None), 'FreeImage_GetHeight': (ctypes.c_int, None), 'FreeImage_GetWidth': (ctypes.c_int, None), 'FreeImage_GetImageType': (ctypes.c_int, None), 'FreeImage_GetBPP': (ctypes.c_int, None), 'FreeImage_GetColorsUsed': (ctypes.c_int, None), 'FreeImage_ConvertTo32Bits': (ctypes.c_void_p, None), 'FreeImage_GetPitch': (ctypes.c_int, None), 'FreeImage_Unload': (ctypes.c_void_p, None)}
    def __init__(self):
        self._lib = None
        self._lock = threading.RLock()
        self._messages = []
        if sys.platform.startswith('win'):
            functype = ctypes.WINFUNCTYPE
        else:
            functype = ctypes.CFUNCTYPE
        @functype(None, ctypes.c_int, ctypes.c_char_p)
        def error_handler(fif, message):
            message = message.decode('utf-8')
            self._messages.append(message)
            while len(self._messages) > 256:
                self._messages.pop(0)
        self._error_handler = error_handler
    @property
    def lib(self):
        if self._lib is None:
            try:
                self.load_freeimage()
            except OSError as err:
                self._lib = 'The freeimage library could not be loaded: '
                self._lib += str(err)
        if isinstance(self._lib, str):
            raise RuntimeError(self._lib)
        return self._lib
    def has_lib(self):
        try:
            self.lib
        except Exception:
            return False
        return True
    def load_freeimage(self):
        """Try to load the freeimage lib from the system. If not successful,
        try to download the imageio version and try again.
        """
        success = False
        try:
            self._load_freeimage()
            self._register_api()
            if self.lib.FreeImage_GetVersion().decode('utf-8') >= '3.15':
                success = True
        except OSError:
            pass
        if not success:
            get_freeimage_lib()
            self._load_freeimage()
            self._register_api()
        self.lib.FreeImage_SetOutputMessage(self._error_handler)
        self.lib_version = self.lib.FreeImage_GetVersion().decode('utf-8')
    def _load_freeimage(self):
        lib_names = ['freeimage', 'libfreeimage']
        exact_lib_names = ['FreeImage', 'libfreeimage.dylib', 'libfreeimage.so', 'libfreeimage.so.3']
        res_dirs = resource_dirs()
        plat = get_platform()
        if plat:
            fname = FNAME_PER_PLATFORM[plat]
            for dir in res_dirs:
                exact_lib_names.insert(0, os.path.join(dir, 'freeimage', fname))
        lib = os.getenv('IMAGEIO_FREEIMAGE_LIB', None)
        if lib is not None:
            exact_lib_names.insert(0, lib)
        try:
            lib, fname = load_lib(exact_lib_names, lib_names, res_dirs)
        except OSError as err:
            err_msg = str(err) + """
Please install the FreeImage library."""
            raise OSError(err_msg)
        self._lib = lib
        self.lib_fname = fname
    def _register_api(self):
        for f, (restype, argtypes) in self._API.items():
            func = getattr(self.lib, f)
            func.restype = restype
            func.argtypes = argtypes
    def __enter__(self):
        self._lock.acquire()
        return self.lib
    def __exit__(self, *args):
        self._show_any_warnings()
        self._lock.release()
    def _reset_log(self):
        """Reset the list of output messages. Call this before
        loading or saving an image with the FreeImage API.
        """
        self._messages = []
    def _get_error_message(self):
        """Get the output messages produced since the last reset as
        one string. Returns 'No known reason.' if there are no messages.
        Also resets the log.
        """
        if self._messages:
            res = ' '.join(self._messages)
            self._reset_log()
            return res
        else:
            return 'No known reason.'
    def _show_any_warnings(self):
        """If there were any messages since the last reset, show them
        as a warning. Otherwise do nothing. Also resets the messages.
        """
        if self._messages:
            logger.warning('imageio.freeimage warning: ' + self._get_error_message())
            self._reset_log()
            return None
        else:
            return None
    def get_output_log(self):
        """Return a list of the last 256 output messages
        (warnings and errors) produced by the FreeImage library.
        """
        return [m for m in self._messages]
    def getFIF(self, filename, mode, bb=None):
        """Get the freeimage Format (FIF) from a given filename.
        If mode is 'r', will try to determine the format by reading
        the file, otherwise only the filename is used.

        This function also tests whether the format supports reading/writing.
        """
        with self as lib:
            ftype = -1
            if mode not in 'rw':
                raise ValueError('Invalid mode (must be "r" or "w").')
            elif mode == 'r':
                if bb is not None:
                    fimemory = lib.FreeImage_OpenMemory(ctypes.c_char_p(bb), len(bb))
                    ftype = lib.FreeImage_GetFileTypeFromMemory(ctypes.c_void_p(fimemory), len(bb))
                    lib.FreeImage_CloseMemory(ctypes.c_void_p(fimemory))
                if ftype == -1 and os.path.isfile(filename):
                    ftype = lib.FreeImage_GetFileType(efn(filename), 0)
            if ftype == -1:
                ftype = lib.FreeImage_GetFIFFromFilename(efn(filename))
            if ftype == -1:
                raise ValueError('Cannot determine format of file "%s"' % filename)
            elif mode == 'w' and not lib.FreeImage_FIFSupportsWriting(ftype):
                raise ValueError('Cannot write the format of file "%s"' % filename)
            elif not (mode == 'r' and not lib.FreeImage_FIFSupportsReading(ftype)):
                raise ValueError('Cannot read the format of file "%s"' % filename)
            else:
                return ftype
    def create_bitmap(self, filename, ftype, flags=0):
        """create_bitmap(filename, ftype, flags=0)
        Create a wrapped bitmap object.
        """
        return FIBitmap(self, filename, ftype, flags)
    def create_multipage_bitmap(self, filename, ftype, flags=0):
        """create_multipage_bitmap(filename, ftype, flags=0)
        Create a wrapped multipage bitmap object.
        """
        return FIMultipageBitmap(self, filename, ftype, flags)
class FIBaseBitmap(object):
    def __init__(self, fi, filename, ftype, flags):
        self._fi = fi
        self._filename = filename
        self._ftype = ftype
        self._flags = flags
        self._bitmap = None
        self._close_funcs = []
    def __del__(self):
        self.close()
    def close(self):
        if self._bitmap is not None:
            if self._close_funcs:
                for close_func in self._close_funcs:
                    try:
                        with self._fi:
                            fun = close_func[0]
                            fun(*close_func[1:])
                    except Exception:
                        pass
                self._close_funcs = []
                self._bitmap = None
                return None
    def _set_bitmap(self, bitmap, close_func=None):
        """Function to set the bitmap and specify the function to unload it."""
        if self._bitmap is not None:
            pass
        if close_func is None:
            close_func = (self._fi.lib.FreeImage_Unload, bitmap)
        self._bitmap = bitmap
        if close_func:
            self._close_funcs.append(close_func)
            return None
        else:
            return None
    def get_meta_data(self):
        models = [(name[5:], number) for name, number in METADATA_MODELS.__dict__.items() if name.startswith('FIMD_')]
        metadata = Dict()
        tag = ctypes.c_void_p()
        with self._fi as lib:
            for model_name, number in models:
                mdhandle = lib.FreeImage_FindFirstMetadata(number, self._bitmap, ctypes.byref(tag))
                mdhandle = ctypes.c_void_p(mdhandle)
                if mdhandle:
                    more = True
                    while more:
                        tag_name = lib.FreeImage_GetTagKey(tag).decode('utf-8')
                        tag_type = lib.FreeImage_GetTagType(tag)
                        byte_size = lib.FreeImage_GetTagLength(tag)
                        char_ptr = ctypes.c_char * byte_size
                        data = char_ptr.from_address(lib.FreeImage_GetTagValue(tag))
                        tag_bytes = bytes(bytearray(data))
                        tag_val = tag_bytes
                        if tag_type == METADATA_DATATYPE.FIDT_ASCII:
                            tag_val = tag_bytes.decode('utf-8', 'replace')
                        elif tag_type in METADATA_DATATYPE.dtypes:
                            dtype = METADATA_DATATYPE.dtypes[tag_type]
                            if IS_PYPY and isinstance(dtype, (list, tuple)):
                                pass
                            else:
                                try:
                                    tag_val = numpy.frombuffer(tag_bytes, dtype=dtype).copy()
                                    if len(tag_val) == 1:
                                        tag_val = tag_val[0]
                                except Exception:
                                    pass
                        subdict = metadata.setdefault(model_name, Dict())
                        subdict[tag_name] = tag_val
                        more = lib.FreeImage_FindNextMetadata(mdhandle, ctypes.byref(tag))
                    lib.FreeImage_FindCloseMetadata(mdhandle)
            return metadata
    def set_meta_data(self, metadata):
        models = {}
        for name, number in METADATA_MODELS.__dict__.items():
            if name.startswith('FIMD_'):
                models[name[5:]] = number
        def get_tag_type_number(dtype):
            for number, numpy_dtype in METADATA_DATATYPE.dtypes.items():
                if dtype == numpy_dtype:
                    return number
        with self._fi as lib:
            for model_name, subdict in metadata.items():
                number = models.get(model_name, None)
                if number is None:
                    continue
                for tag_name, tag_val in subdict.items():
                    tag = lib.FreeImage_CreateTag()
                    tag = ctypes.c_void_p(tag)
                    try:
                        is_ascii = False
                        if isinstance(tag_val, str):
                            try:
                                tag_bytes = tag_val.encode('ascii')
                                is_ascii = True
                            except UnicodeError:
                                pass
                        if is_ascii:
                            tag_type = METADATA_DATATYPE.FIDT_ASCII
                            tag_count = len(tag_bytes)
                        else:
                            if not hasattr(tag_val, 'dtype'):
                                tag_val = numpy.array([tag_val])
                            tag_type = get_tag_type_number(tag_val.dtype)
                            if tag_type is None:
                                logger.warning('imageio.freeimage warning: Could not determine tag type of %r.' % tag_name)
                                continue
                            tag_bytes = tag_val.tobytes()
                            tag_count = tag_val.size
                            lib.FreeImage_SetTagKey(tag, tag_name.encode('utf-8'))
                            lib.FreeImage_SetTagType(tag, tag_type)
                            lib.FreeImage_SetTagCount(tag, tag_count)
                            lib.FreeImage_SetTagLength(tag, len(tag_bytes))
                            lib.FreeImage_SetTagValue(tag, tag_bytes)
                            tag_key = lib.FreeImage_GetTagKey(tag)
                            lib.FreeImage_SetMetadata(number, self._bitmap, tag_key, tag)
                    except Exception as err:
                        logger.warning(f'imagio.freeimage warning: Could not set tag {tag_name!r}: {self._fi._get_error_message()!s}, {str(err)!s}')
                    finally:
                        lib.FreeImage_DeleteTag(tag)
            return None
class FIBitmap(FIBaseBitmap):
    __doc__ = 'Wrapper for the FI bitmap object.'
    def allocate(self, array):
        assert isinstance(array, numpy.ndarray)
        shape = array.shape
        dtype = array.dtype
        r, c = shape[:2]
        if len(shape) == 2:
            n_channels = 1
        elif len(shape) == 3:
            n_channels = shape[2]
        else:
            n_channels = shape[0]
        try:
            fi_type = FI_TYPES.fi_types[dtype.type, n_channels]
            self._fi_type = fi_type
        except KeyError:
            raise ValueError('Cannot write arrays of given type and shape.')
        with self._fi as lib:
            bpp = 8 * dtype.itemsize * n_channels
            bitmap = lib.FreeImage_AllocateT(fi_type, c, r, bpp, 0, 0, 0)
            bitmap = ctypes.c_void_p(bitmap)
            if not bitmap:
                raise RuntimeError('Could not allocate bitmap for storage: %s' % self._fi._get_error_message())
            self._set_bitmap(bitmap, (lib.FreeImage_Unload, bitmap))
            return None
    def load_from_filename(self, filename=None):
        if filename is None:
            filename = self._filename
        with self._fi as lib:
            bitmap = lib.FreeImage_Load(self._ftype, efn(filename), self._flags)
            bitmap = ctypes.c_void_p(bitmap)
            if not bitmap:
                raise ValueError(f'Could not load bitmap "{self._filename!s}": {self._fi._get_error_message()!s}')
            self._set_bitmap(bitmap, (lib.FreeImage_Unload, bitmap))
            return None
    def save_to_filename(self, filename=None):
        if filename is None:
            filename = self._filename
        ftype = self._ftype
        bitmap = self._bitmap
        fi_type = self._fi_type
        with self._fi as lib:
            if fi_type == FI_TYPES.FIT_BITMAP:
                can_write = lib.FreeImage_FIFSupportsExportBPP(ftype, lib.FreeImage_GetBPP(bitmap))
            else:
                can_write = lib.FreeImage_FIFSupportsExportType(ftype, fi_type)
            if not can_write:
                raise TypeError('Cannot save image of this format to this file type')
            res = lib.FreeImage_Save(ftype, bitmap, efn(filename), self._flags)
            if res is None:
                raise RuntimeError(f'Could not save file `{self._filename}`: {self._fi._get_error_message()}')
            return None
    def get_image_data(self):
        dtype, shape, bpp = self._get_type_and_shape()
        array = self._wrap_bitmap_bits_in_array(shape, dtype, False)
        with self._fi as lib:
            isle = lib.FreeImage_IsLittleEndian()
        def n(arr):
            if arr.ndim == 1:
                return arr[::-1].T
            elif arr.ndim == 2:
                return arr[:, ::-1].T
            elif arr.ndim == 3:
                return arr[:, :, ::-1].T
            elif arr.ndim == 4:
                return arr[:, :, :, ::-1].T
        if len(shape) == 3 and isle and dtype.type == numpy.uint8:
            b = n(array[0])
            g = n(array[1])
            r = n(array[2])
            if shape[0] == 3:
                return numpy.dstack((r, g, b))
            elif shape[0] == 4:
                a = n(array[3])
                return numpy.dstack((r, g, b, a))
            else:
                raise ValueError('Cannot handle images of shape %s' % shape)
        a = n(array).copy()
        return a
    def set_image_data(self, array):
        assert isinstance(array, numpy.ndarray)
        shape = array.shape
        dtype = array.dtype
        with self._fi as lib:
            isle = lib.FreeImage_IsLittleEndian()
        r, c = shape[:2]
        if len(shape) == 2:
            n_channels = 1
            w_shape = (c, r)
        elif len(shape) == 3:
            n_channels = shape[2]
            w_shape = (n_channels, c, r)
        else:
            n_channels = shape[0]
        def n(arr):
            return arr[::-1].T
        wrapped_array = self._wrap_bitmap_bits_in_array(w_shape, dtype, True)
        if len(shape) == 3 and isle and dtype.type == numpy.uint8:
            R = array[:, :, 0]
            G = array[:, :, 1]
            B = array[:, :, 2]
            wrapped_array[0] = n(B)
            wrapped_array[1] = n(G)
            wrapped_array[2] = n(R)
            if shape[2] == 4:
                A = array[:, :, 3]
                wrapped_array[3] = n(A)
        else:
            wrapped_array[:] = n(array)
        if self._need_finish:
            self._finish_wrapped_array(wrapped_array)
        if len(shape) == 2:
            if dtype.type == numpy.uint8:
                with self._fi as lib:
                    palette = lib.FreeImage_GetPalette(self._bitmap)
                palette = ctypes.c_void_p(palette)
                if not palette:
                    raise RuntimeError('Could not get image palette')
                try:
                    palette_data = GREY_PALETTE.ctypes.data
                except Exception:
                    palette_data = GREY_PALETTE.__array_interface__['data'][0]
                ctypes.memmove(palette, palette_data, 1024)
    def _wrap_bitmap_bits_in_array(self, shape, dtype, save):
        """Return an ndarray view on the data in a FreeImage bitmap. Only
        valid for as long as the bitmap is loaded (if single page) / locked
        in memory (if multipage). This is used in loading data, but
        also during saving, to prepare a strided numpy array buffer.

        """
        with self._fi as lib:
            pitch = lib.FreeImage_GetPitch(self._bitmap)
            bits = lib.FreeImage_GetBits(self._bitmap)
        height = shape[-1]
        byte_size = height * pitch
        itemsize = dtype.itemsize
        if len(shape) == 3:
            strides = (itemsize, shape[0] * itemsize, pitch)
        else:
            strides = (itemsize, pitch)
        data = (ctypes.c_char * byte_size).from_address(bits)
        try:
            self._need_finish = False
            if TEST_NUMPY_NO_STRIDES:
                raise NotImplementedError()
            return numpy.ndarray(shape, dtype=dtype, buffer=data, strides=strides)
        except NotImplementedError:
            if save:
                self._need_finish = True
                return numpy.zeros(shape, dtype=dtype)
                return None
            else:
                bb = bytes(bytearray(data))
                array = numpy.frombuffer(bb, dtype=dtype).copy()
                if len(shape) == 3:
                    array.shape = (shape[2], strides[-1] // shape[0], shape[0])
                    array2 = array[:shape[2], :shape[1], :shape[0]]
                    array = numpy.zeros(shape, dtype=array.dtype)
                    for i in range(shape[0]):
                        array[i] = array2[:, :, i].T
                else:
                    array.shape = (shape[1], strides[-1])
                    array = array[:shape[1], :shape[0]].T
                return array
    def _finish_wrapped_array(self, array):
        """Hardcore way to inject numpy array in bitmap."""
        with self._fi as lib:
            pitch = lib.FreeImage_GetPitch(self._bitmap)
            bits = lib.FreeImage_GetBits(self._bitmap)
            bpp = lib.FreeImage_GetBPP(self._bitmap)
        newshape = (array.shape[-1], realwidth, nchannels)
        array2 = numpy.zeros(newshape, array.dtype)
        if nchannels == 1:
            array2[:, :array.shape[-2], 0] = array.T
        else:
            for i in range(nchannels):
                array2[:, :array.shape[-2], i] = array[i, :, :].T
        data_ptr = array2.__array_interface__['data'][0]
        ctypes.memmove(bits, data_ptr, array2.nbytes)
        del array2
    def _get_type_and_shape(self):
        bitmap = self._bitmap
        with self._fi as lib:
            w = lib.FreeImage_GetWidth(bitmap)
            h = lib.FreeImage_GetHeight(bitmap)
            self._fi_type = lib.FreeImage_GetImageType(bitmap)
            if not fi_type:
                raise ValueError('Unknown image pixel type')
        bpp = None
        dtype = FI_TYPES.dtypes[fi_type]
        if fi_type == FI_TYPES.FIT_BITMAP:
            with self._fi as lib:
                bpp = lib.FreeImage_GetBPP(bitmap)
                has_pallette = lib.FreeImage_GetColorsUsed(bitmap)
            if has_pallette:
                if has_pallette == 256:
                    palette = lib.FreeImage_GetPalette(bitmap)
                    palette = ctypes.c_void_p(palette)
                    p = (ctypes.c_uint8 * 1024).from_address(palette.value)
                    p = numpy.frombuffer(p, numpy.uint32).copy()
                    if (GREY_PALETTE == p).all():
                        extra_dims = []
                        return (numpy.dtype(dtype), extra_dims + [w, h], bpp)
                newbitmap = lib.FreeImage_ConvertTo32Bits(bitmap)
                newbitmap = ctypes.c_void_p(newbitmap)
                self._set_bitmap(newbitmap)
                return self._get_type_and_shape()
            elif bpp == 8:
                extra_dims = []
            elif bpp == 24:
                extra_dims = [3]
            elif bpp == 32:
                extra_dims = [4]
            else:
                newbitmap = lib.FreeImage_ConvertTo32Bits(bitmap)
                newbitmap = ctypes.c_void_p(newbitmap)
                self._set_bitmap(newbitmap)
                return self._get_type_and_shape()
        else:
            extra_dims = FI_TYPES.extra_dims[fi_type]
        return (numpy.dtype(dtype), extra_dims + [w, h], bpp)
    def quantize(self, quantizer=0, palettesize=256):
        """Quantize the bitmap to make it 8-bit (paletted). Returns a new
        FIBitmap object.
        Only for 24 bit images.
        """
        with self._fi as lib:
            bitmap = lib.FreeImage_ColorQuantizeEx(self._bitmap, quantizer, palettesize, 0, None)
            bitmap = ctypes.c_void_p(bitmap)
            if not bitmap:
                raise ValueError(f'Could not quantize bitmap "{self._filename!s}": {self._fi._get_error_message()!s}')
            new = FIBitmap(self._fi, self._filename, self._ftype, self._flags)
            new._set_bitmap(bitmap, (lib.FreeImage_Unload, bitmap))
            new._fi_type = self._fi_type
            return new
class FIMultipageBitmap(FIBaseBitmap):
    __doc__ = 'Wrapper for the multipage FI bitmap object.'
    def load_from_filename(self, filename=None):
        if filename is None:
            filename = self._filename
        create_new = False
        read_only = True
        keep_cache_in_memory = False
        with self._fi as lib:
            multibitmap = lib.FreeImage_OpenMultiBitmap(self._ftype, efn(filename), create_new, read_only, keep_cache_in_memory, self._flags)
            multibitmap = ctypes.c_void_p(multibitmap)
            if not multibitmap:
                err = self._fi._get_error_message()
                raise ValueError(f'Could not open file "{self._filename!s}" as multi-image: {err!s}')
            self._set_bitmap(multibitmap, (lib.FreeImage_CloseMultiBitmap, multibitmap))
            return None
    def save_to_filename(self, filename=None):
        if filename is None:
            filename = self._filename
        create_new = True
        read_only = False
        keep_cache_in_memory = False
        with self._fi as lib:
            multibitmap = lib.FreeImage_OpenMultiBitmap(self._ftype, efn(filename), create_new, read_only, keep_cache_in_memory, 0)
            multibitmap = ctypes.c_void_p(multibitmap)
            if not multibitmap:
                msg = f'Could not open file "{self._filename!s}" for writing multi-image: {self._fi._get_error_message()!s}'
                raise ValueError(msg)
            self._set_bitmap(multibitmap, (lib.FreeImage_CloseMultiBitmap, multibitmap))
            return None
    def __len__(self):
        with self._fi as lib:
            return lib.FreeImage_GetPageCount(self._bitmap)
    def get_page(self, index):
        """Return the sub-bitmap for the given page index.
        Please close the returned bitmap when done.
        """
        with self._fi as lib:
            bitmap = lib.FreeImage_LockPage(self._bitmap, index)
            bitmap = ctypes.c_void_p(bitmap)
            if not bitmap:
                raise ValueError('Could not open sub-image %i in %r: %s' % (index, self._filename, self._fi._get_error_message()))
            bm = FIBitmap(self._fi, self._filename, self._ftype, self._flags)
            bm._set_bitmap(bitmap, (lib.FreeImage_UnlockPage, self._bitmap, bitmap, False))
            return bm
    def append_bitmap(self, bitmap):
        """Add a sub-bitmap to the multi-page bitmap."""
        with self._fi as lib:
            lib.FreeImage_AppendPage(self._bitmap, bitmap._bitmap)
            return None
fi = Freeimage()
