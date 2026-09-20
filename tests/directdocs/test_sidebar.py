#! /usr/bin/env python3
"""The module neighbourhood the sidebar shows on an API page.

The set's sidebar is bounded to two levels of the global table of contents,
because the full tree is most of a megabyte on every one of several thousand
pages.  That leaves a page deep in the tree -- ``OpenGL.GL.ARB.base_instance``
-- with nothing in the sidebar naming the package it is in or the extensions
beside it.  :func:`neighbourhood` is what fills that in, from the docnames
alone.
"""

import pyopengl_sidebar

DOCNAMES = frozenset(
    {
        'index',
        'api/index',
        'api/OpenGL',
        'api/OpenGL.GL',
        'api/OpenGL.GL.ARB',
        'api/OpenGL.GL.ARB.base_instance',
        'api/OpenGL.GL.ARB.bindless_texture',
        'api/OpenGL.GL.ARB.compute_shader',
        'api/OpenGL.GL.EXT',
        'api/OpenGL.GL.EXT.abgr',
        'api/OpenGL.GL.shaders',
        'api/OpenGL.Tk',
        'api/OpenGL.Tk.widget',
        'reference/index',
    }
)


class TestAncestors:
    def test_they_run_from_the_root_down_to_the_parent(self):
        found = pyopengl_sidebar.neighbourhood(
            'api/OpenGL.GL.ARB.base_instance', DOCNAMES
        )
        assert [name for name, _doc in found.ancestors] == [
            'OpenGL',
            'OpenGL.GL',
            'OpenGL.GL.ARB',
        ]

    def test_an_ancestor_with_no_page_is_left_out(self):
        """A package nothing documented is not a link to nowhere."""
        found = pyopengl_sidebar.neighbourhood(
            'api/OpenGL.GL.ARB.base_instance', DOCNAMES - {'api/OpenGL.GL'}
        )
        assert [name for name, _doc in found.ancestors] == [
            'OpenGL',
            'OpenGL.GL.ARB',
        ]

    def test_the_root_module_has_none(self):
        found = pyopengl_sidebar.neighbourhood('api/OpenGL', DOCNAMES)
        assert found.ancestors == ()


class TestSiblings:
    def test_they_are_the_other_modules_in_the_same_package(self):
        found = pyopengl_sidebar.neighbourhood(
            'api/OpenGL.GL.ARB.base_instance', DOCNAMES
        )
        assert [name for name, _doc, _here in found.siblings] == [
            'base_instance',
            'bindless_texture',
            'compute_shader',
        ]

    def test_the_current_page_is_marked_among_them(self):
        found = pyopengl_sidebar.neighbourhood(
            'api/OpenGL.GL.ARB.base_instance', DOCNAMES
        )
        assert [here for _name, _doc, here in found.siblings] == [
            True,
            False,
            False,
        ]

    def test_a_deeper_module_is_not_one(self):
        """One level only: ``OpenGL.GL.ARB.base_instance`` is not beside ``ARB``."""
        found = pyopengl_sidebar.neighbourhood('api/OpenGL.GL.ARB', DOCNAMES)
        assert [name for name, _doc, _here in found.siblings] == [
            'ARB',
            'EXT',
            'shaders',
        ]


class TestChildren:
    def test_a_package_lists_what_is_directly_inside_it(self):
        found = pyopengl_sidebar.neighbourhood('api/OpenGL.Tk', DOCNAMES)
        assert [name for name, _doc in found.children] == ['widget']

    def test_a_module_has_none(self):
        found = pyopengl_sidebar.neighbourhood('api/OpenGL.Tk.widget', DOCNAMES)
        assert found.children == ()


class TestWhereItApplies:
    def test_a_narrative_page_has_no_neighbourhood(self):
        """Only the generated module pages sit in a tree of dotted names."""
        assert pyopengl_sidebar.neighbourhood('index', DOCNAMES) is None
        assert pyopengl_sidebar.neighbourhood('reference/index', DOCNAMES) is None

    def test_the_api_index_has_none_either(self):
        assert pyopengl_sidebar.neighbourhood('api/index', DOCNAMES) is None
