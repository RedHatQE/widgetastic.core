# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from xml.sax.saxutils import quoteattr, unescape


def quote(s):
    """Quotes a string in such a way that it is usable inside XPath expressions."""
    return unescape(quoteattr(s))
