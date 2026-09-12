#! /usr/bin/env python3
"""Where a job has two implementations, both of them do the whole job.

PyOpenGL is supported with and without the compiled extension, with and
without numpy, and on the ctypes entry points or the C ones.  Every one of
those is a pair of implementations of the same interface, and the way a pair
goes wrong is that one of them quietly does less:

* ``glGenVertexArrays(1)`` asks the output handler for one name's worth of
  array and passes the length as a number, which is what ``numpy.zeros``
  takes.  The ctypes handlers took only a sequence, so on an installation
  without numpy the plainest call there is answered ``TypeError: 'int' object
  is not reversible`` before it reached the driver -- and with accelerate
  installed that was 256 of the suite's cases, every one of them setting up
  its context.
* ``OpenGL_accelerate``'s ``_ErrorChecker`` carries ``checkContext``, the
  switch its check actually reads, and ``OpenGL.error``'s carried no such
  name.  The case that would have said so asked only the build that had it,
  and turned the ``AttributeError`` from the build that did not into a skip --
  so on every ``accel0`` run it reported three skips whose reason was the
  defect.

``tests/bindings/dispatch/test_attribute_surface.py`` already compares the two
dispatch implementations across 1,266 entry points, and
``tests/bindings/errors/test_context_checking.py`` asks both error checkers.
This is the same question asked of the array format handlers, which are the
other place a pair of implementations meets a caller: one per array library,
each registered against the types it converts, and one of them compiled.

Read from the registry rather than from the class tree.  The accelerated numpy
handler is a Cython type that does not inherit from ``FormatHandler`` at all,
so a check that walked ``__subclasses__`` would miss exactly the implementation
most callers get.
"""

import inspect

import pytest

from OpenGL.arrays.formathandler import FormatHandler


def registry():
    """The handlers actually registered, by the name each was loaded under."""
    from OpenGL.arrays.arraydatatype import ArrayDatatype

    FormatHandler.loadAll()
    found = {}
    for key, handler in ArrayDatatype.getRegistry().items():
        if isinstance(key, str):
            found[key] = handler
    return found


#: What a handler is asked to do.  Declared on ``FormatHandler`` as a body-less
#: method each implementation fills in, so the base class is the statement of
#: the interface and this is read off it.
def protocol():
    wanted = {}
    for name, value in vars(FormatHandler).items():
        if name.startswith('_') or not inspect.isfunction(value):
            continue
        if isinstance(vars(FormatHandler).get(name), (classmethod, staticmethod)):
            continue
        wanted[name] = value
    return wanted


#: Methods the base class defines for every handler rather than declaring for
#: each to fill in, so an implementation inheriting them is complete.
PROVIDED = frozenset(['register', 'registerReturn'])


def _takes_anything(signature):
    """Whether `signature` has a ``*args`` or ``**kwargs`` in it."""
    return any(
        parameter.kind
        in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
        for parameter in signature.parameters.values()
    )


def _arity(signature, skip_self):
    """``(fewest, most)`` positional arguments a call may pass."""
    parameters = [
        parameter
        for name, parameter in signature.parameters.items()
        if not (skip_self and name == 'self')
    ]
    most = len(parameters)
    fewest = sum(
        1 for parameter in parameters if parameter.default is inspect.Parameter.empty
    )
    return fewest, most


class TestEveryRegisteredHandlerDoesTheWholeJob:
    def test_the_registry_holds_more_than_one_implementation(self):
        """A comparison over one implementation compares nothing."""
        found = registry()
        assert len(found) > 1, sorted(found)

    def test_every_handler_answers_every_part_of_the_protocol(self):
        wanted = set(protocol()) - PROVIDED
        assert wanted, 'FormatHandler declares no interface to check'
        missing = []
        for name, handler in sorted(registry().items()):
            for method in sorted(wanted):
                if getattr(handler, method, None) is None:
                    missing.append('%s has no %s' % (name, method))
        assert not missing, (
            'these registered array handlers do not implement the whole of '
            'the FormatHandler interface, so a call that reaches one of them '
            'through the part it is missing answers AttributeError from '
            'inside the conversion machinery rather than doing the '
            'conversion:\n  %s' % '\n  '.join(missing)
        )

    def test_every_handler_takes_the_arguments_the_interface_declares(self):
        """A method that takes fewer arguments is a caller's TypeError.

        How many, rather than what they are called: every handler here spells
        the first one ``instance`` where the interface says ``value``, and
        nothing calls any of these by keyword, so the names are a house style
        rather than a contract.  How many a call may pass is the contract, and
        it is what went wrong: the ctypes output handlers took a sequence
        where numpy's took a length.

        Only where the implementation can be asked: a Cython method carries no
        signature, and ``inspect`` raises rather than guessing -- which is
        itself the reason a compiled handler needs the case above.
        """
        wanted = protocol()
        complaints = []
        for name, handler in sorted(registry().items()):
            for method, declaration in sorted(wanted.items()):
                if method in PROVIDED:
                    continue
                implementation = getattr(handler, method, None)
                if implementation is None:
                    continue                # the case above reports it
                try:
                    taken = inspect.signature(implementation)
                except (TypeError, ValueError):
                    continue                # compiled, and says nothing
                declared = inspect.signature(declaration)
                if _takes_anything(taken):
                    continue
                fewest, most = _arity(declared, skip_self=True)
                takes_fewest, takes_most = _arity(taken, skip_self=False)
                # At least what the interface declares.  Taking more is a
                # handler being lenient about something nobody following the
                # interface will pass; taking fewer is a call that works
                # against one implementation and raises against the other.
                if takes_fewest > fewest or takes_most < most:
                    complaints.append(
                        '%s.%s takes %d to %d argument(s) and the interface '
                        'declares %d to %d: %s against %s'
                        % (
                            name, method,
                            takes_fewest, takes_most, fewest, most,
                            list(taken.parameters),
                            [one for one in declared.parameters if one != 'self'],
                        )
                    )
        assert not complaints, (
            'these registered array handlers cannot take a call the '
            'FormatHandler interface says they take, so a call that works '
            'where one library is installed fails where the other is:\n  %s'
            % '\n  '.join(complaints)
        )


class TestTheRegistryAnswersTheSameQuestionsEitherWay:
    """``FormatHandler.typeLookup`` is how a third party asks which handler
    its own array format resolved to, and it reads the registry by type.

    The pure-Python registry is a dict subclass and answered; the compiled one
    held its mapping privately and offered only ``__setitem__``, so the lookup
    raised ``TypeError: 'HandlerRegistry' object is not subscriptable``
    wherever the accelerators are installed -- which is most installations.
    Its own ``except KeyError`` could not catch that, so what a caller got was
    an error about the registry's type rather than the answer or the
    ``KeyError`` the method documents.
    """

    def test_a_type_nothing_handles_raises_the_documented_error(self):
        import ctypes

        with pytest.raises(KeyError):
            FormatHandler.typeLookup(type('NotAnArray', (), {}))
        with pytest.raises(KeyError):
            FormatHandler.typeLookup(ctypes.c_uint * 3)

    def test_the_registry_reads_back_what_was_registered(self):
        from OpenGL.arrays.arraydatatype import ArrayDatatype

        FormatHandler.loadAll()
        found = ArrayDatatype.getRegistry()
        assert len(found), 'nothing registered, so the lookup proves nothing'
        for key in found.keys():
            assert key in found
            assert found[key] is found.get(key)


class TestTheOutputHandlersTakeALengthOrAShape:
    """``glGenVertexArrays(1)`` passes a length; ``numpy.zeros`` takes one.

    The ctypes handlers took only a sequence, so the plainest call there is
    failed on an installation without numpy -- and with accelerate installed
    that was 256 of the suite's cases, every one setting up its context.  The
    two have to answer the same call or a program that runs where numpy is
    installed stops running where it is not.
    """

    @pytest.mark.parametrize('shape', [1, (1,), 3, (3,)])
    def test_every_output_handler_allocates_from_either(self, shape):
        from OpenGL.arrays import GLuintArray

        answered = GLuintArray.zeros(shape)
        assert GLuintArray.arraySize(answered) == (
            shape if isinstance(shape, int) else shape[0]
        )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
