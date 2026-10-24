"""The one error a Tk GL context raises.

A separate class lets an application catch it and fall back to another
backend.  Context creation can fail on a working system.  A driver may lack
``ARB_create_context``, a platform may have no implementation here, or a
request for eight multisample samples may not be available.
"""

__all__ = ['TkContextError']


class TkContextError(RuntimeError):
    """A GL context could not be created for, or bound to, a Tk widget"""
