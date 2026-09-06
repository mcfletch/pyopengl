"""The types the generated stubs annotate arrays with.

A stub-only module: nothing imports it at run time, and the stubs beside every
generated module read it rather than each declaring these for themselves.
"""

import ctypes
import sys
from collections.abc import Sequence
from typing import Any, TypeAlias

if sys.version_info >= (3, 12):
    from collections.abc import Buffer
else:  # PEP 688 arrived in 3.12; before it there is no way to say "buffer".
    from typing_extensions import Buffer

# What may be passed where an array is wanted.  Wide, but not Any:
# `Any | X` is `Any` to a type checker, and a union containing it
# checks nothing while looking as though it does.  Buffer (PEP 688)
# is what admits a numpy array, which is neither a Sequence nor a
# memoryview to a checker.  None is a null pointer where one is
# meaningful.
ByteArray: TypeAlias = Sequence[Any] | Buffer | ctypes._CData | None
DoubleArray: TypeAlias = Sequence[Any] | Buffer | ctypes._CData | None
FloatArray: TypeAlias = Sequence[Any] | Buffer | ctypes._CData | None
Int64Array: TypeAlias = Sequence[Any] | Buffer | ctypes._CData | None
IntArray: TypeAlias = Sequence[Any] | Buffer | ctypes._CData | None
ShortArray: TypeAlias = Sequence[Any] | Buffer | ctypes._CData | None
UByteArray: TypeAlias = Sequence[Any] | Buffer | ctypes._CData | None
UInt64Array: TypeAlias = Sequence[Any] | Buffer | ctypes._CData | None
UIntArray: TypeAlias = Sequence[Any] | Buffer | ctypes._CData | None
UShortArray: TypeAlias = Sequence[Any] | Buffer | ctypes._CData | None
AnyArray: TypeAlias = Sequence[Any] | Buffer | ctypes._CData | None

# What is *returned*.  Any, because the shape of the result
# follows the *value* of an argument rather than its type:
# glGenTextures(1) hands back a scalar and glGenTextures(3)
# an array, and neither is a Sequence -- a numpy array does
# not register as one.  Naming a container here makes the
# ordinary call, whose result goes straight into the next
# entry point as an int, an error in the caller's report.
ByteArrayResult: TypeAlias = Any
DoubleArrayResult: TypeAlias = Any
FloatArrayResult: TypeAlias = Any
Int64ArrayResult: TypeAlias = Any
IntArrayResult: TypeAlias = Any
ShortArrayResult: TypeAlias = Any
UByteArrayResult: TypeAlias = Any
UInt64ArrayResult: TypeAlias = Any
UIntArrayResult: TypeAlias = Any
UShortArrayResult: TypeAlias = Any
AnyArrayResult: TypeAlias = Any
