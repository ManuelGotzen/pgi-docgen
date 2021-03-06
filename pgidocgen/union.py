# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import os

from . import util
from .fields import FieldsMixin


class UnionGenerator(util.Generator, FieldsMixin):
    def __init__(self):
        self._unions = {}
        self._methods = {}

    def get_names(self):
        return ["unions/index.rst"]

    def is_empty(self):
        return not bool(self._unions)

    def add_union(self, obj, code):
        if isinstance(code, unicode):
            code = code.encode("utf-8")
        self._unions[obj] = code

    def add_method(self, cls_obj, obj, code):
        if isinstance(code, unicode):
            code = code.encode("utf-8")

        if cls_obj in self._methods:
            self._methods[cls_obj].append((obj, code))
        else:
            self._methods[cls_obj] = [(obj, code)]

    def write(self, dir_, module_fileobj):
        sub_dir = os.path.join(dir_, "unions")
        path = os.path.join(sub_dir, "index.rst")

        os.mkdir(sub_dir)

        unions = self._unions.keys()

        def indent(c):
            return "\n".join(["    %s" % l for l in c.splitlines()])

        # write the code
        for cls in unions:
            module_fileobj.write(self._unions[cls])
            methods = self._methods.get(cls, [])
            def sort_func(e):
                return util.is_normalmethod(e[0]), e[0].__name__
            methods.sort(key=sort_func)

            for obj, code in methods:
                module_fileobj.write(indent(code) + "\n")

        index_handle = open(path, "wb")
        index_handle.write(util.make_rest_title("Unions") + "\n\n")

        # add classes to the index toctree
        index_handle.write(".. toctree::\n    :maxdepth: 1\n\n")
        for cls in sorted(unions, key=lambda x: x.__name__):
            index_handle.write("""\
    %s
""" % cls.__name__)

        for cls in unions:
            h = open(os.path.join(sub_dir, cls.__name__) + ".rst", "wb")
            name = cls.__module__ + "." + cls.__name__
            title = name
            h.write(util.make_rest_title(title, "=") + "\n")

            # Fields
            self.write_field_table(cls, h)

            h.write("""
Methods
-------

""")

            methods = self._methods.get(cls, [])
            if not methods:
                h.write("None\n\n")
            else:
                h.write(".. autosummary::\n\n")

            # sort static methods first, then by name
            def sort_func(e):
                return util.is_normalmethod(e[0]), e[0].__name__
            methods.sort(key=sort_func)
            for obj, code in methods:
                h.write("    " + cls.__module__ + "." + cls.__name__ +
                        "." + obj.__name__ + "\n")

            # Details
            h.write("""
Details
-------

""")

            if util.is_base(cls):
                h.write("""
.. autoclass:: %s
    :members:
    :undoc-members:
""" % name)
            else:
                h.write("""
.. autoclass:: %s
    :show-inheritance:
    :members:
    :undoc-members:
""" % name)

            h.close()

        index_handle.close()
