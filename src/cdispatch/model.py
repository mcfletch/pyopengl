"""One record per entry point, and everything the generator emits is a field in it.

The grammar, from ``plans/C-DISPATCH.md``::

    command   := name, feature, deprecated, return-kind, [parameter]
    parameter := name, c-type, direction, size-spec, retain?, element-type?
    direction := in | out | in-out
    size-spec := none | fixed(N) | from-arg(index, divisor)
               | glget-table(pname-arg) | image(format-arg, type-arg, dims)
               | string-array | computed(<helper>)

The registry supplies the types and the parameter names; the annotation file
supplies ``direction``, ``size`` and ``retain``.  The C, the ``.pyi`` and the
docstrings all read this one description.
"""

from dataclasses import dataclass, field

from . import ctypes_model as cm

__all__ = [
    'IN',
    'OUT',
    'IN_OUT',
    'NO_SIZE',
    'Fixed',
    'FromArg',
    'GLGetTable',
    'ImageSize',
    'TypedArray',
    'StringArray',
    'Computed',
    'Parameter',
    'Command',
]

IN = 'in'
OUT = 'out'
IN_OUT = 'in-out'


class _SizeSpec:
    """Base for the size-spec variants, so ``isinstance`` can group them."""

    #: True when the generator can emit the size without a hand-written helper.
    declarative = True


@dataclass(frozen=True)
class _NoSize(_SizeSpec):
    """The parameter's length is not checked and not computed."""

    def __repr__(self):
        return 'NO_SIZE'


NO_SIZE = _NoSize()


@dataclass(frozen=True)
class Fixed(_SizeSpec):
    """A constant element count, from ``setInputArraySize(name, N)``."""

    count: int


@dataclass(frozen=True)
class FromArg(_SizeSpec):
    """``count = argument // divisor``.

    Covers both ``setInputArraySize(name, other)`` and the whole lambda space
    of the friendly layer, which is three bodies differing only in ``divisor``.
    """

    argument: int
    divisor: int = 1


@dataclass(frozen=True)
class GLGetTable(_SizeSpec):
    """The size comes from the generated pname table, keyed on an argument."""

    pname_argument: int


@dataclass(frozen=True)
class ImageSize(_SizeSpec):
    """Size is a function of format, type, dimensions and pixel-store state."""

    format_argument: int
    type_argument: int
    dimensions: tuple = ()
    declarative = False


@dataclass(frozen=True)
class TypedArray(_SizeSpec):
    """The element type is a value the caller passes, not a fixed type.

    ``glDrawElements(mode, count, type, indices)`` says what its indices are
    made of in ``type``; the client-side array pointers do the same, and the
    GL additionally keeps their memory after the call returns.
    """

    #: Which argument carries the GL constant, or -1 where there is none.
    type_argument: int = -1


@dataclass(frozen=True)
class StringArray(_SizeSpec):
    """A ``str`` or a list of them becomes ``char **`` plus a length array."""

    declarative = False


@dataclass(frozen=True)
class Computed(_SizeSpec):
    """One of the hand-written Tier 3 helpers computes the size."""

    helper: str
    declarative = False


#: C keywords and common macro names that appear as registry parameter names.
_RESERVED = frozenset(
    [
        'near',
        'far',
        'auto',
        'break',
        'case',
        'char',
        'const',
        'continue',
        'default',
        'do',
        'double',
        'else',
        'enum',
        'extern',
        'float',
        'for',
        'goto',
        'if',
        'inline',
        'int',
        'long',
        'register',
        'restrict',
        'return',
        'short',
        'signed',
        'sizeof',
        'static',
        'struct',
        'switch',
        'typedef',
        'union',
        'unsigned',
        'void',
        'volatile',
        'while',
    ]
)


@dataclass
class Parameter:
    """One argument of one entry point."""

    name: str
    ctype: cm.CType
    direction: str = IN
    size: _SizeSpec = NO_SIZE
    retain: bool = False
    #: Where this output falls in the returned tuple.  It is the order the
    #: friendly layer annotated the outputs in, which is not always the order
    #: the C signature declares them in.
    output_order: int = 0

    @property
    def c_name(self):
        """The identifier the generated C uses, avoiding keyword collisions."""
        if self.name in _RESERVED or not self.name.isidentifier():
            return '_%s' % (self.name,)
        return self.name

    @property
    def is_array(self):
        """True when the argument arrives as a buffer rather than a value."""
        return self.ctype.pointers > 0 and not self.is_string_pointer

    @property
    def is_string_pointer(self):
        """``const GLchar *const*`` — a list of strings, not an array of them."""
        return self.ctype.pointers > 1 and self.ctype.base in ('GLchar', 'GLcharARB')

    @property
    def is_output(self):
        return self.direction in (OUT, IN_OUT)

    @property
    def element(self):
        """The element description for an array parameter."""
        return cm.element_type(self.ctype.base if self.ctype.pointers == 1 else '')

    @property
    def macro(self):
        """The converter macro for a scalar parameter."""
        return cm.scalar_macro(self.ctype)


@dataclass
class Command:
    """One entry point, and everything needed to emit its stub."""

    name: str
    return_type: cm.CType
    parameters: list = field(default_factory=list)
    #: The feature or extension that first required it, for ``extension``.
    feature: str = ''
    deprecated: str = ''
    #: Names a hand-written Tier 3 body rather than a generated one.
    helper: str = ''
    #: The one-line purpose, when its source licence has been cleared.
    purpose: str = ''
    #: Which registry API the command belongs to: gl, gles1, gles2, glx, wgl.
    api: str = 'gl'
    #: True where the friendly layer stores an argument against the context,
    #: because the GL keeps reading it after the call returns.
    retains: bool = False

    @property
    def arg_names(self):
        return [parameter.name for parameter in self.parameters]

    @property
    def returns_void(self):
        return cm.is_void(self.return_type)

    @property
    def stub_name(self):
        return 'pygl_%s' % (self.name,)

    @property
    def array_count(self):
        """How many cleanup-frame slots the stub needs."""
        return len([p for p in self.parameters if p.is_array or p.is_string_pointer])

    @property
    def output_parameters(self):
        """The outputs, in the order they contribute to the return value."""
        return sorted(
            (p for p in self.parameters if p.is_output),
            key=lambda parameter: parameter.output_order,
        )

    @property
    def python_arguments(self):
        """Every name the Python signature accepts, output parameters included.

        ``orPassIn`` is the normal path rather than an exception, so an output
        parameter is an optional trailing argument rather than an absent one.
        """
        return [p.name for p in self.parameters]

    @property
    def required_arguments(self):
        """The arguments a caller must supply."""
        return [p.name for p in self.parameters if not p.is_output]

    @property
    def tier(self):
        """Which implementation tier of the plan this command falls in."""
        if self.helper:
            return 3
        for parameter in self.parameters:
            if not parameter.size.declarative:
                return 3
        for parameter in self.parameters:
            if parameter.size is not NO_SIZE or parameter.is_output:
                return 2
        return 1

    def signature_line(self):
        """The docstring's first line, from the record alone."""
        arguments = ', '.join(self.required_arguments)
        outputs = [p.name for p in self.output_parameters]
        if outputs:
            result = ', '.join(outputs)
        elif self.returns_void:
            result = 'None'
        else:
            result = self.return_type.base
        return '%s(%s) -> %s' % (self.name, arguments, result)

    def text_signature(self):
        """``__text_signature__``, so ``inspect.signature()`` answers."""
        parts = list(self.required_arguments)
        parts.extend('%s=None' % (p.name,) for p in self.output_parameters)
        parts.append('/')
        return '($module, %s)' % (', '.join(parts),)
