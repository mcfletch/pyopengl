"""GBM device and surface helpers for selecting an EGL rendering device.

GBM (Generic Buffer Management) is the Linux library that allocates graphics
buffers on a DRM device.  The code is based on PyOpenGL GitHub issue #6, by
@abandoned-cocoon.
"""
import weakref, ctypes, logging, os, glob
from OpenGL.platform import ctypesloader
from OpenGL import _opaque
log = logging.getLogger(__name__)
try:
    gbm = ctypesloader.loadLibrary(ctypes.CDLL,"gbm")
except OSError as err:
    # Every function here wraps libgbm, so the module cannot work without it.
    # ImportError lets a caller guard the import as optional.
    raise ImportError("OpenGL.EGL.gbmdevice needs the gbm library: %s" % (err,)) from err
__all__ = ('enumerate_devices','open_device','close_device','gbm')
_DEVICE_HANDLES = {}
GBM_BO_USE_SCANOUT = (1 << 0)
GBM_BO_USE_CURSOR = (1 << 1)
GBM_BO_USE_CURSOR_64X64 = GBM_BO_USE_CURSOR
GBM_BO_USE_RENDERING = (1 << 2)
GBM_BO_USE_WRITE = (1 << 3)
GBM_BO_USE_LINEAR = (1 << 4)

GBMDevice = _opaque.opaque_pointer_cls('GBMDevice')
GBMSurface = _opaque.opaque_pointer_cls('GBMSurface')
gbm.gbm_create_device.restype = GBMDevice
gbm.gbm_surface_create.restype = GBMSurface

def filter_bad_drivers(cards, bad_drivers=('nvidia',)):
    """Return ``cards`` without the cards whose driver is in ``bad_drivers``.

    The default excludes nvidia devices.
    """
    # The lookup uses /dev/dri/by-path/pci-*, so a GPU that is not on the PCI
    # bus is never excluded.  No other way to match a card to its driver is
    # known.
    bad_cards = set()
    for link in glob.glob('/dev/dri/by-path/pci-*-card'):
        base = os.path.basename(link)
        pci_id = base[4:-5]
        driver = os.path.basename(os.readlink('/sys/bus/pci/devices/%s/driver'%(pci_id,)))
        if driver in bad_drivers:
            card = os.path.basename(os.readlink(link))
            log.debug("Skipping %s because it uses %s driver",card,driver)
            bad_cards.add(card)
    filtered = [
        card for card in cards 
        if os.path.basename(card) not in bad_cards
    ]
    # assert len(filtered) == 1, filtered
    return filtered

def enumerate_devices():
    """Return the paths of the gbm devices on the system, sorted.

    Cards using an nvidia driver are removed with :func:`filter_bad_drivers`.
    """
    import glob
    # gbm says card* is the correct entry point...
    return filter_bad_drivers(sorted(glob.glob('/dev/dri/card*')))
def open_device(path):
    """Open a particular gbm device
    
    * path - integer index into :func:`enumerate_devices`, a device
      basename (`renderD128`), or a full path as returned from
      :func:`enumerate_devices`

    Raises at least:

    * RuntimeError for an invalid index
    * IOError/OSError when the device cannot be opened
    * RuntimeError when GBM cannot create the device

    The caller must pass the result to :func:`close_device`, which closes the
    file handle and frees the ``gbm_device``.

    Returns a GBMDevice, an opaque pointer.
    """
    if isinstance(path,int):
        try:
            devices = enumerate_devices()
            path = devices[path]
        except IndexError:
            raise RuntimeError('Only %s devices available, cannot use 0-index %s'%(len(devices),path)) from None
    else:
        path = os.path.join('/dev/dri',path) # allow for specifying "renderD128"
    log.debug("Final device path: %s", path)
    # Read-write, because the driver maps buffers through this descriptor, and
    # a write-only descriptor refuses a readable mapping.  Mode 'w' would
    # create a missing file and truncate an existing one.
    fh = open(path,'r+b',buffering=0)  # noqa: OGC121 a DRM device node, opened for its descriptor; nothing is read or written through the file object
    dev = gbm.gbm_create_device(fh.fileno())
    if dev == 0:
        fh.close()
        raise RuntimeError('Unable to create rendering device for: %s'%(path))
    _DEVICE_HANDLES[dev] = fh
    return dev
def close_device(device):
    """Close an opened gbm device"""
    gbm.gbm_device_destroy(device)
    try:
        handle = _DEVICE_HANDLES.pop(device)
        handle.close()
    except KeyError:
        pass

def create_surface(device, width=512, height=512, format=None, flags=GBM_BO_USE_RENDERING):
    """Create a GBM surface on the given device.

    device - opaque GBMDevice pointer
    width,height - dimensions in pixels
    format - EGL_NATIVE_VISUAL_ID from an EGL configuration
    flags - ``GBM_BO_USE_*`` flags for how the buffer will be read and
            written

    Returns a GBMSurface opaque pointer.
    """
    if not format:
        raise ValueError(
            'Use eglGetConfigAttrib(display,config,EGL_NATIVE_VISUAL_ID) to get the native surface format',
        )
    return gbm.gbm_surface_create(device, width, height, format, flags)