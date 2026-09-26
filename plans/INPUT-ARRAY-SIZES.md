# Input arrays measured against their count

Status: 🟡 Partial (2026-09-24)

## The defect

An input array whose length the driver reads from another argument is passed
through unmeasured. `glViewportArrayv(first, count, v)` reads `count * 4`
floats from `v`; handed a shorter array, the driver reads past the end of the
caller's buffer. The generated friendly modules record each such parameter as
a comment, `# INPUT glViewportArrayv.v size not checked against 'count'`, and
there are 1,333 of those comments in `OpenGL/` (a command declared by both a
core version and an extension carries one in each module).

## What landed

The mechanism, and the viewport-array family that
[openglcontext/plans/MULTI-VIEW-RENDERING.md](../../openglcontext/plans/MULTI-VIEW-RENDERING.md)
depends on.

- The size spec. `model.FromArg` carries a `multiplier`, and the annotation
  table's `from-argument` kind records it where it is not one:
  `{"kind": "from-argument", "argument": "count", "divisor": 1, "multiplier": 4}`.
- The rule. For an input, a `from-argument` size is a minimum: the driver reads
  that many elements, and a longer array is a caller's larger buffer. `None`
  is refused unless the count is zero. A fixed size stays exact.
- The C path. `PYGL_ARRAY_IN_MIN(i, name, element, count, per)` and
  `pygl_array_in_min` in `accelerate/src/c/`, emitted by `emit_c` for an
  input `FromArg`. The count is widened to `Py_ssize_t` before the multiply.
- The ctypes path. `Wrapper.setInputArrayCount(argName, countArg, multiplier)`
  and `arrayhelpers.AsArrayTypedCountChecked`, applied by
  `_declarations.customise_entry` from the same table entry. `GLProc` answers
  `setInputArrayCount` as already implemented.
- Both honour `ARRAY_SIZE_CHECKING`.
- Annotated: `glViewportArrayv`, `glScissorArrayv`, `glDepthRangeArrayv`,
  `glDepthRangeArraydvNV`, `glMulticastViewportArrayvNVX`,
  `glMulticastScissorArrayvNVX`, `glScissorExclusiveArrayvNV` (GL and GLES2),
  and the GLES2 `NV` and `OES` viewport-array entry points. Three of these
  (`glDepthRangeArraydvNV`, `glDepthRangeArrayfvNV`, `glDepthRangeArrayfvOES`)
  had no annotation at all, so the ctypes path handed their `v` to ctypes
  unconverted.
- Tests: `tests/bindings/arrays/test_input_array_counts.py` (every annotated
  entry point, both implementations, no context needed),
  `tests/gl/test_gl41.py::TestViewportArraysAreMeasuredAgainstTheCount`
  (against a driver), and the generator cases in `tests/cdispatch/`.

### Arrays of strings (2026-09-24)

A `GLchar *const *` the driver reads `count` pointers from is the same defect
with worse consequences: `None` for a positive count had the driver read from
address zero, and `glGetUniformIndices(program, 3)` in the friendly form did
exactly that and dumped core (`plans/CODE-REVIEW-2026-09-24.md`, finding 1).

- The table records the count as `from-argument` on the string parameter of
  `glCompileShaderIncludeARB.path`, `glCreateShaderProgramv(EXT).strings`,
  `glTransformFeedbackVaryings(EXT).varyings` and
  `glGetUniformIndices.uniformNames`, across GL, GLES2 and GLES3.
  `glShaderSource` is not annotated: its friendly form counts the strings
  itself, so its count cannot disagree with them.
- The C emits `PYGL_STRING_ARRAY_MIN(i, name, count)`, and
  `pygl_string_array_min` refuses fewer strings than `count`, or `None` for a
  positive count. A pointer array the caller built is passed unmeasured.
- The ctypes path applies `arrayhelpers.StringArrayCountChecked` through
  `Wrapper.setInputArrayCount`, which recognises a `StringArray` argument.
  `GL_3_0`, `GLES3_3_0` and `GLES3_3_1` are not customised from the table, so
  their chains state `setInputArrayCount` themselves, and
  `cdispatch.extract` reads that call from a chain.
- The annotation table writes `divisor` and `multiplier` on every
  `from-argument` size, and the ctypes path sizes an output
  `count * multiplier // divisor`, as the C does.
- Tests: `tests/bindings/arrays/test_input_array_counts.py` (`STRINGS`, both
  implementations, no context), `tests/gl/test_uniform_indices.py` against a
  driver.

## Still open

The rest of the 1,321 comments, in three groups by what the registry says:

1. `count*N` with a literal `N` (300 comments): `glUniform4fv`,
   `glProgramUniformMatrix4fv` and the rest of the uniform and program-uniform
   setters. The registry states the multiplier, so these are table entries and
   no new code. Thirty-nine of them are in `GL_4_1.py`.
2. A bare argument name (537): `n`, `count`, `bufSize`, `size`, `primcount`.
   The same kind with a multiplier of one. `bufSize` and `size` name bytes
   rather than elements for some commands, so each wants reading against its
   specification before it is annotated.
3. `COMPSIZE(...)` (493): the registry says the size is computed and not how.
   `COMPSIZE(pname)` on an input (`glTexParameterfv`, `glLightfv`) is the
   `glget-table` lookup applied to an input; `COMPSIZE(count)` is this
   document's family, each needing its multiplier from the specification;
   `COMPSIZE(count,type)` and similar are element-type dependent, like
   `typed-array`.

Each group is red/green against `test_input_array_counts.py`'s pattern: a
short array refused on both paths, before the call.
