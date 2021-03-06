# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.


import unittest

from pgidocgen.repo import Repository


class TRepository(unittest.TestCase):

    def test_pango(self):
        repo = Repository("Pango", "1.0")

        self.assertTrue(
            repo.lookup_parameter_docs("Pango.extents_to_pixels.inclusive"))

        self.assertTrue(
            repo.lookup_parameter_docs("Pango.break_.text"))

        self.assertTrue(
            repo.lookup_parameter_docs("Pango.TabArray.new.initial_size"))

        self.assertTrue(repo.is_private("Pango.RendererPrivate"))
        self.assertFalse(repo.is_private("Pango.AttrIterator"))

    def test_glib_shadowed(self):
        repo = Repository("GLib", "2.0")

        # GLib.io_add_watch points to g_io_add_watch_full and should
        # also use its docs

        self.assertTrue(
            repo.lookup_parameter_docs("GLib.io_add_watch.priority"))

        self.assertTrue(
            "priority" in repo.lookup_attr_docs("GLib.io_add_watch"))

        # we include a note containing the shadowed docs
        self.assertTrue(
            ".. note::" in repo.lookup_attr_docs("GLib.io_add_watch"))

    def test_gio(self):
        repo = Repository("Gio", "2.0")

        method = repo.lookup_attr_docs("Gio.Application.activate")
        signal = repo.lookup_signal_docs("Gio.Application.activate")

        self.assertTrue(method)
        self.assertTrue(signal)
        self.assertNotEqual(method, signal)

        self.assertFalse(
            repo.lookup_parameter_docs(
                "Gio.Application.command-line.command_line"))

        self.assertTrue(
            repo.lookup_parameter_docs(
                "Gio.Application.command-line.command_line", signal=True))

    def test_returns(self):
        repo = Repository("Gio", "2.0")

        ret = repo.lookup_return_docs("Gio.File.load_contents_finish")
        self.assertTrue(ret.strip())

    def test_vfuns(self):
        repo = Repository("Gtk", "3.0")

        ret = repo.lookup_attr_docs("Gtk.TreeModel.do_get_iter")
        self.assertTrue(ret.strip())

    def test_other(self):
        Repository("GLib", "2.0")
        Repository("GObject", "2.0")

    def test_version_added(self):
        repo = Repository("Atk", "1.0")
        docs = repo.lookup_attr_meta("Atk.Document.get_attributes")
        self.assertTrue(".. versionadded:: 1.12" in docs)

        docs = repo.lookup_attr_meta("Atk.Document.get_attribute_value")
        self.assertTrue(".. versionadded:: 1.12" in docs)

    def test_deprecated(self):
        repo = Repository("Atk", "1.0")
        docs = repo.lookup_attr_meta("Atk.Hyperlink.is_selected_link")
        self.assertTrue(".. deprecated::" in docs)

    def test_webkit2(self):
        from gi.repository import WebKit2

        repo = Repository("Atk", "1.0")
        # contains signal named "print", which needs special handling
        repo.parse_signals(WebKit2.WebView)

    def test_props(self):
        from pgi.repository import Gtk

        repo = Repository("Gtk", "3.0")
        self.assertTrue(repo.parse_properties(Gtk.Button))
        self.assertTrue(repo.parse_signals(Gtk.Button))

    def test_child_props(self):
        from pgi.repository import Gtk

        repo = Repository("Gtk", "3.0")
        repo.parse_child_properties(Gtk.Paned)
        repo.parse_child_properties(Gtk.ActionBar)
