#! /usr/bin/env python3
"""Which context is current, as something that outlives its handle.

A context handle is an address, and the driver hands addresses out again: a
suite of three hundred contexts reuses a couple of dozen.  So the handle alone
cannot say whether the context behind it is the one that made a buffer, a
texture or a program.  :func:`OpenGL.dispatch.context_identity` can: it is the
same object for as long as a context lives, and a different one once
:func:`OpenGL.dispatch.forget_context` has said that context is gone, whatever
address the next one lands on.
"""

import pytest

from OpenGL import dispatch


@pytest.fixture
def current(monkeypatch):
    """Choose which context the platform says is current, by address."""
    monkeypatch.setattr(dispatch, '_identities', {}, raising=False)

    def choose(address):
        monkeypatch.setattr(dispatch, '_current_context', lambda: address)

    return choose


def test_it_is_the_same_while_the_context_lives(current):
    current(0x1234)
    assert dispatch.context_identity() is dispatch.context_identity()


def test_two_contexts_are_told_apart(current):
    current(0x1234)
    first = dispatch.context_identity()
    current(0x5678)
    assert dispatch.context_identity() is not first


def test_a_context_made_current_again_is_still_itself(current):
    current(0x1234)
    first = dispatch.context_identity()
    current(0x5678)
    dispatch.context_identity()
    current(0x1234)
    assert dispatch.context_identity() is first


def test_a_context_on_a_forgotten_ones_address_is_a_new_one(current):
    """What the handle cannot say: the address is the same, the context is not."""
    current(0x1234)
    gone = dispatch.context_identity()
    dispatch.forget_context(0x1234)
    assert dispatch.context_identity() is not gone


@pytest.mark.parametrize('nothing', [0, None])
def test_there_is_none_with_no_context_current(current, nothing):
    """0 where the platform says none is current, None where it cannot say."""
    current(nothing)
    assert dispatch.context_identity() is None


def test_it_is_part_of_the_public_surface():
    assert 'context_identity' in dispatch.__all__


class TestContextsThatShareObjects:
    """Contexts made to share their buffers, textures and programs are one namespace.

    A name made in one is the same object in the others, so the identity that
    says whose names these are is the group's.
    """

    def test_a_shared_context_has_the_identity_of_the_one_it_shares_with(self, current):
        current(0x1234)
        main = dispatch.context_identity()
        dispatch.share_context(0x5678, with_handle=0x1234)
        current(0x5678)
        assert dispatch.context_identity() is main

    def test_a_context_not_in_the_group_is_still_told_apart(self, current):
        current(0x1234)
        main = dispatch.context_identity()
        dispatch.share_context(0x5678, with_handle=0x1234)
        current(0x9ABC)
        assert dispatch.context_identity() is not main

    def test_the_context_shared_with_may_not_have_been_current_yet(self, current):
        dispatch.share_context(0x5678, with_handle=0x1234)
        current(0x5678)
        shared = dispatch.context_identity()
        current(0x1234)
        assert dispatch.context_identity() is shared

    def test_forgetting_the_shared_context_leaves_the_group_as_it_was(self, current):
        current(0x1234)
        main = dispatch.context_identity()
        dispatch.share_context(0x5678, with_handle=0x1234)
        dispatch.forget_context(0x5678)
        current(0x1234)
        assert dispatch.context_identity() is main

    def test_a_context_destroyed_and_its_address_reused_is_not_in_the_group(self, current):
        current(0x1234)
        main = dispatch.context_identity()
        dispatch.share_context(0x5678, with_handle=0x1234)
        dispatch.forget_context(0x5678)
        current(0x5678)
        assert dispatch.context_identity() is not main

    def test_the_group_outlives_the_context_it_began_with(self, current):
        current(0x1234)
        main = dispatch.context_identity()
        dispatch.share_context(0x5678, with_handle=0x1234)
        dispatch.forget_context(0x1234)
        current(0x5678)
        assert dispatch.context_identity() is main

    def test_a_handle_is_shared_with_itself_harmlessly(self, current):
        current(0x1234)
        main = dispatch.context_identity()
        dispatch.share_context(0x1234, with_handle=0x1234)
        assert dispatch.context_identity() is main


def test_sharing_is_part_of_the_public_surface():
    assert 'share_context' in dispatch.__all__
