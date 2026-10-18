"""The few Objective-C messages Tk on Aqua needs, sent through ctypes.

A GL context is attached to an ``NSView`` on macOS, and the only way to reach
one from Python without a binding package is the Objective-C runtime:
``objc_getClass`` finds a class, ``sel_registerName`` a selector, and
``objc_msgSend`` sends the message.  :class:`Runtime` wraps those three and
nothing else, so ``OpenGL.Tk`` adds no dependency for it.

**``objc_msgSend`` has no signature of its own.**  The caller's declaration of
the arguments and the result is what gets compiled into the call, so each
message here names its argument and result types and a function pointer of that
shape is built once per shape.  A struct passed by value (an ``NSRect``) works
that way too.  Struct results are not used: on Intel they come back through
``objc_msgSend_stret`` and on Apple silicon through ``objc_msgSend``, and
nothing here needs to read one.

**An Objective-C exception ends the process.**  Nothing in ctypes can catch
one, so a message sent to an object that does not answer it is a crash rather
than an error, and :meth:`Runtime.responds` is how a caller asks first.

**The reference counts are the caller's.**  ``alloc`` and ``init`` return an
object the caller owns and has to :meth:`Runtime.release`; anything else
returned by a message is autoreleased, which is what :meth:`Runtime.pool` is
for -- Tk's own event loop drains a pool per event, but a call made from
Python between events has none unless it makes one.

Importing this module touches no library; :func:`runtime` loads the Objective-C
runtime and AppKit on first use and raises :class:`CocoaError` where there are
none.
"""

from __future__ import annotations

import contextlib
import ctypes
import ctypes.util
import sys
from typing import Any, Iterator, Optional

__all__ = ['CGRect', 'CocoaError', 'Runtime', 'runtime']

APPKIT = '/System/Library/Frameworks/AppKit.framework/AppKit'
LIBOBJC = '/usr/lib/libobjc.A.dylib'


class CocoaError(RuntimeError):
    """The Objective-C runtime is not there, or does not know a class"""


class CGRect(ctypes.Structure):
    """``NSRect`` as it is on a 64-bit Mac: four doubles, origin then size"""

    _fields_ = [
        ('x', ctypes.c_double),
        ('y', ctypes.c_double),
        ('width', ctypes.c_double),
        ('height', ctypes.c_double),
    ]


#: ``BOOL`` is a ``bool`` on Apple silicon and a ``signed char`` on Intel;
#: either is one byte holding zero or one, which an unsigned byte reads and
#: writes the same on both.
BOOL = ctypes.c_ubyte
NSUInteger = ctypes.c_ulong
NSInteger = ctypes.c_long
ID = ctypes.c_void_p


class Runtime:
    """Messages to Objective-C objects

    Objects are plain integers (the address) or ``None`` for ``nil``; classes
    are looked up by name with :meth:`cls`.  A message names its selector and,
    where it takes arguments or answers anything but an object, the ctypes
    types of each::

        rt = runtime()
        view = rt.send(rt.send(rt.cls('NSView'), 'alloc'), 'init')
        rt.send(view, 'setHidden:', True, argtypes=(BOOL,), restype=None)
    """

    def __init__(self, objc: Any, appkit: Any = None) -> None:
        self._objc = objc
        self._appkit = appkit
        self._selectors: dict[str, int] = {}
        self._senders: dict[tuple, Any] = {}
        objc.objc_getClass.argtypes = [ctypes.c_char_p]
        objc.objc_getClass.restype = ID
        objc.sel_registerName.argtypes = [ctypes.c_char_p]
        objc.sel_registerName.restype = ID
        objc.object_getClass.argtypes = [ID]
        objc.object_getClass.restype = ID
        objc.class_getName.argtypes = [ID]
        objc.class_getName.restype = ctypes.c_char_p
        objc.class_respondsToSelector.argtypes = [ID, ID]
        objc.class_respondsToSelector.restype = BOOL
        objc.objc_autoreleasePoolPush.argtypes = []
        objc.objc_autoreleasePoolPush.restype = ctypes.c_void_p
        objc.objc_autoreleasePoolPop.argtypes = [ctypes.c_void_p]
        objc.objc_autoreleasePoolPop.restype = None
        self._msgSend = ctypes.cast(objc.objc_msgSend, ctypes.c_void_p).value

    ### lookup
    def cls(self, name: str) -> int:
        """The class called ``name``; :class:`CocoaError` where there is none"""
        found = self._objc.objc_getClass(name.encode('ascii'))
        if not found:
            raise CocoaError('The Objective-C class %s is not loaded' % (name,))
        return int(found)

    def selector(self, name: str) -> int:
        """The selector called ``name``, as ``sel_registerName`` answers it"""
        found = self._selectors.get(name)
        if found is None:
            found = self._selectors[name] = int(
                self._objc.sel_registerName(name.encode('ascii')))
        return found

    def className(self, receiver: int) -> str:
        """The name of the class ``receiver`` is an instance of"""
        name = self._objc.class_getName(self._objc.object_getClass(receiver))
        return (name or b'').decode('ascii', 'replace')

    def responds(self, receiver: int, name: str) -> bool:
        """Whether ``receiver`` answers the message ``name``"""
        return bool(self._objc.class_respondsToSelector(
            self._objc.object_getClass(receiver), self.selector(name)))

    ### messages
    def send(
        self,
        receiver: Optional[int],
        name: str,
        *arguments: Any,
        argtypes: tuple = (),
        restype: Any = ID,
    ) -> Any:
        """Send ``name`` to ``receiver`` and answer what it returns

        ``argtypes`` are the ctypes types of ``arguments``, one each; a
        ``restype`` of ``None`` is a message answering ``void``.  A message to
        ``nil`` answers zero, as it does in Objective-C.  An object result
        comes back as an ``int``, or ``None`` for ``nil``.
        """
        if len(arguments) != len(argtypes):
            raise TypeError(
                '%s was given %d arguments and %d types for them'
                % (name, len(arguments), len(argtypes)))
        shape = (restype, tuple(argtypes))
        sender = self._senders.get(shape)
        if sender is None:
            prototype = ctypes.CFUNCTYPE(restype, ID, ID, *argtypes)
            sender = self._senders[shape] = prototype(self._msgSend)
        result = sender(receiver, self.selector(name), *arguments)
        if restype is ID:
            return int(result) if result else None
        return result

    def new(self, className: str) -> int:
        """``[[Class alloc] init]``; the caller owns the result"""
        made = self.send(self.send(self.cls(className), 'alloc'), 'init')
        if not made:
            raise CocoaError('%s would not initialise' % (className,))
        return made

    def retain(self, receiver: Optional[int]) -> None:
        """Take a reference to ``receiver``"""
        if receiver:
            self.send(receiver, 'retain')

    def release(self, receiver: Optional[int]) -> None:
        """Give a reference back; ``nil`` is nothing to give"""
        if receiver:
            self.send(receiver, 'release', restype=None)

    ### strings and arrays
    def string(self, text: str) -> int:
        """An autoreleased ``NSString`` holding ``text``"""
        made = self.send(
            self.cls('NSString'), 'stringWithUTF8String:',
            text.encode('utf-8'), argtypes=(ctypes.c_char_p,))
        if not made:
            raise CocoaError('NSString would not hold %r' % (text,))
        return made

    def text(self, string: Optional[int]) -> str:
        """The Python string an ``NSString`` holds; empty for ``nil``"""
        if not string:
            return ''
        raw = self.send(string, 'UTF8String', restype=ctypes.c_char_p)
        return (raw or b'').decode('utf-8', 'replace')

    def items(self, array: Optional[int]) -> list[int]:
        """The objects in an ``NSArray``, in order"""
        if not array:
            return []
        count = self.send(array, 'count', restype=NSUInteger)
        return [
            self.send(array, 'objectAtIndex:', index,
                      argtypes=(NSUInteger,))
            for index in range(count)
        ]

    @contextlib.contextmanager
    def pool(self) -> Iterator[None]:
        """An autorelease pool for the length of the block

        What a message returns without the caller owning it lives until the
        nearest pool drains.  With none in place the runtime prints a
        complaint for each such object and leaks it.
        """
        token = self._objc.objc_autoreleasePoolPush()
        try:
            yield
        finally:
            self._objc.objc_autoreleasePoolPop(token)


_runtime: Optional[Runtime] = None


def runtime() -> Runtime:
    """The shared :class:`Runtime`, loading the libraries on first use

    AppKit is loaded by name so the classes in it can be found even in a
    process that has not opened a window yet; Tk has done so already in any
    process that has a widget.
    """
    global _runtime
    if _runtime is None:
        if sys.platform != 'darwin':
            raise CocoaError('The Objective-C runtime is a macOS facility')
        try:
            objc = ctypes.cdll.LoadLibrary(
                ctypes.util.find_library('objc') or LIBOBJC)
            appkit = ctypes.cdll.LoadLibrary(APPKIT)
        except OSError as error:
            raise CocoaError(
                'Could not load the Objective-C runtime: %s' % (error,)
            ) from error
        _runtime = Runtime(objc, appkit)
    return _runtime
