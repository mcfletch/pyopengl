"""The one error a Tk GL context raises.

Its own class rather than ``RuntimeError`` so an application can offer another
backend when a context cannot be had -- which is a normal thing to happen, not
a bug: a driver may have no ``ARB_create_context``, a platform may have no
implementation here yet, and a request for eight multisample samples may simply
not be available.
"""

__all__ = ['TkContextError']


class TkContextError(RuntimeError):
    """A GL context could not be created for, or bound to, a Tk widget"""
