# -*- coding: utf-8 -*-
# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import re

from BeautifulSoup import BeautifulStoneSoup, Tag

from . import util
from .util import escape_rest, force_unindent


def _handle_data(types, current, d):

    scanner = re.Scanner([
        (r"\*?@[A-Za-z0-9_]+", lambda scanner, token:("PARAM", token)),
        (r"[#%]?[A-Za-z0-9_:\-]+\**", lambda scanner, token:("ID", token)),
        (r"\(", lambda scanner, token:("OTHER", token)),
        (r"\)", lambda scanner, token:("OTHER", token)),
        (r",", lambda scanner, token:("OTHER", token)),
        (r"\s", lambda scanner, token:("SPACE", token)),
        (r"[^\s]+", lambda scanner, token:("OTHER", token)),
    ])

    results, remainder = scanner.scan(d)
    assert not remainder

    objects = {
        "NULL": "None",
        "TRUE": "True",
        "FALSE": "False",
        "gint": "int",
        "gboolean": "bool",
        "gchar": "str",
        "gdouble": "float",
        "glong": "int",
        "gfloat": "float",
        "guint": "int",
        "gulong": "int",
        "char": "str",
        "gpointer": "object",
    }

    def id_ref(token):
        # possible identifier reference

        # strip pointer
        sub = token.rstrip("*")

        if sub.startswith(("#", "%")):
            sub = sub[1:]

        if sub in objects:
            return ":obj:`%s`" % objects[sub]
        elif sub in types:
            pytype = types[sub]
            assert "." in pytype
            return ":py:obj:`%s`" % pytype
        elif token.startswith(("#", "%")):
            if token.endswith("s"):
                # if we are sure it's a reference and it ends with 's'
                # like "a list of #GtkWindows", we also try "#GtkWindow"
                sub = token[1:-1]
                if sub in types:
                    pytype = types[sub]
                    assert "." in pytype
                    return ":class:`%s <%s>`" % (pytype + "s", pytype)
            else:
                # also try to add "s", GdkFrameTiming(s)
                sub = token[1:] + "s"
                if sub in types:
                    pytype = types[sub]
                    assert "." in pytype
                    py_no_s = pytype[:-1] if pytype[-1] == "s" else pytype
                    return ":class:`%s <%s>`" % (py_no_s, pytype)

        return token

    out = []
    need_space_at_start = False
    for type_, token in results:
        orig_token = token
        if type_ == "PARAM":
            token = token.lstrip("*")
            # paremeter reference
            assert token[0] == "@"
            token = token[1:]
            if token.lower() == token:
                token = "`%s`" % token
            else:
                # some docs use it to reference constants..
                token = id_ref(token)
        elif type_ == "ID":
            parts = re.split("(::?)", token)
            fallback = True
            if len(parts) > 2:
                obj, sep, sigprop = parts[0], parts[1], "".join(parts[2:])
                obj_id = obj.lstrip("#")
                obj_rst_id = types.get(obj_id, current)

                if sigprop and obj_rst_id:
                    fallback = False
                    token = id_ref(obj)
                    is_prop = len(sep) == 1

                    if token:
                        token += " "

                    prop_name = sigprop.replace("_", "-")
                    prop_attr = sigprop.replace("-", "_")
                    if is_prop:
                        rst_target = obj_rst_id + ".props." + prop_attr
                        token += ":py:data:`:%s<%s>`" % (
                            prop_name, rst_target)
                    else:
                        rst_target = obj_rst_id + ".signals." + prop_attr
                        token += ":py:func:`::%s<%s>`" % (
                            prop_name, rst_target)

            if fallback:
                if "-" in token:
                    first, rest = token.split("-", 1)
                    token = id_ref(first) + "-" + rest
                elif token.endswith(":"):
                    token = id_ref(token[:-1]) + ":"
                else:
                    token = id_ref(token)

        changed = orig_token != token

        # nothing changed, escape
        if not changed:
            token = escape_rest(token)

        # insert a space for the previous one
        if need_space_at_start:
            if not token:
                pass
            else:
                # ., is also OK
                if not token.startswith((" ", ".", ",")):
                    token = " " + token
                need_space_at_start = False

        if changed:
            # something changed, we have to make sure that
            # the previous and next character is a space so
            # docutils doesn't get confused wit references
            need_space_at_start = True

        out.append(token)

    return "".join(out)


def _handle_xml(types, current, out, item):
    if isinstance(item, Tag):
        if item.name == "literal" or item.name == "type":
            out.append("``%s``" % item.text)
        elif item.name == "itemizedlist":
            lines = []
            for item in item.contents:
                if not isinstance(item, Tag):
                    continue

                lines.append("* " + " ".join(_handle_data(
                             types, current, item.getText()
                             ).splitlines()))
            out.append("\n\n" + "\n".join(lines) + "\n\n")

        elif item.name == "programlisting":
            text = item.getText()
            if not text.count("\n"):
                out.append("``%s``" % item.getText())
            else:
                code = "\n.. code-block:: c\n\n%s\n" % util.indent(
                    util.unindent(item.getText(), ignore_first_line=True))
                out.append(code)

        elif item.name == "title":
            out.append(_handle_data(types, current, item.getText()))
        elif item.name == "keycombo":
            subs = []
            for sub in item.contents:
                if not isinstance(sub, Tag):
                    continue
                subs.append(_handle_data(types, current, sub.getText()))
            out.append(" + ".join(subs))

        elif item.name == "varlistentry":
            terms = []
            listitem = None
            for sub in item.contents:
                if not isinstance(sub, Tag):
                    continue

                if sub.name == "term":
                    terms.append(sub.getText())
                elif sub.name == "listitem":
                    listitem = sub.getText()
                else:
                    assert 0

            # Poppler-0.18
            if not listitem:
                listitem = ""

            assert terms

            lines = []
            terms_line = ", ".join(
                [_handle_data(types, current, t) for t in terms])
            lines.append("%s\n" % terms_line)
            listitem = force_unindent(listitem, ignore_first_line=True)
            lines.append(
                util.indent(_handle_data(types, current, listitem)) + "\n")
            out.append("\n")
            out.extend(lines)
        else:
            for sub in item.contents:
                _handle_xml(types, current, out, sub)
    else:
        if not out or out[-1].endswith("\n"):
            data = force_unindent(item.string, ignore_first_line=False)
        else:
            data = force_unindent(item.string, ignore_first_line=True)
        out.append(_handle_data(types, current, data))


def docstring_to_rest(types, current, docstring):
    # |[ ]| seems to mark inline code. Move it to docbook so we have a
    # single thing to work with below

    def to_programlisting(match):
        from xml.sax.saxutils import escape
        escaped = escape(match.group(1))
        return "<programlisting>%s</programlisting>" % escaped

    docstring = re.sub("\|\[(.*?)\]\|", to_programlisting,
                       docstring, flags=re.MULTILINE | re.DOTALL)

    # We don't care about para
    docstring = re.sub("<para>", "", docstring)
    docstring = re.sub("</para>", "", docstring)

    soup = BeautifulStoneSoup(docstring,
                              convertEntities=BeautifulStoneSoup.HTML_ENTITIES)
    out = []
    for item in soup.contents:
        _handle_xml(types, current, out, item)

    # make sure to insert spaces between special reST chars
    rst = ""
    while out:
        c = out.pop(0)
        if rst and c:
            last = rst[-1]
            first = c[0]
            if escape_rest(last) != last and escape_rest(first) != first:
                rst += " "
        rst += c

    def fixup_added_since(match):
        return """

.. versionadded:: %s

""" % match.group(1).strip()

    rst = re.sub('@?Since\s*\\\\?:?\s+([^\s]+)$', fixup_added_since, rst)
    return rst
